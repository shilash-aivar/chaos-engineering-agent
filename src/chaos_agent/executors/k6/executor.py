"""k6 load generator — K8s Job when cluster available, simulated otherwise."""

from __future__ import annotations

import logging

from chaos_agent.config import get_settings
from chaos_agent.executors.base import RollbackHandle
from chaos_agent.executors.k6.job import delete_k6_job, launch_k6_job
from chaos_agent.executors.k6.script import build_k6_script
from chaos_agent.models import Fault

logger = logging.getLogger(__name__)


class K6Executor:
    def __init__(self, simulate: bool | None = None) -> None:
        self.simulate = simulate if simulate is not None else get_settings().simulate_execution

    async def apply(
        self,
        experiment_id: str,
        fault: Fault,
        namespace: str,
        max_replica_percent: float,
    ) -> RollbackHandle:
        vus = int(fault.params.get("vus", 30))
        duration = fault.params.get("duration", "5m")
        script = build_k6_script(fault, namespace)
        simulated = self.simulate
        resources = []

        if not simulated:
            ok, resources = await launch_k6_job(
                experiment_id,
                namespace,
                script,
                vus=vus,
                duration=duration,
            )
            if not ok:
                simulated = True
                resources = []

        logger.info(
            "k6_load_started",
            extra={
                "experiment_id": experiment_id,
                "vus": vus,
                "duration": duration,
                "simulate": simulated,
                "job_resources": len(resources),
            },
        )
        return RollbackHandle(
            experiment_id=experiment_id,
            executor="k6",
            resources=resources,
            simulated=simulated,
        )

    async def rollback(self, handle: RollbackHandle) -> None:
        if handle.simulated or not handle.resources:
            logger.info("k6_load_stopped", extra={"experiment_id": handle.experiment_id, "simulated": True})
            return
        job = next((r for r in handle.resources if r.kind == "Job"), None)
        cm = next((r for r in handle.resources if r.kind == "ConfigMap"), None)
        if job and cm:
            await delete_k6_job(job.namespace, job.name, cm.name)
        logger.info("k6_load_stopped", extra={"experiment_id": handle.experiment_id, "simulated": False})
