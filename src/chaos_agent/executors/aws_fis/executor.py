"""AWS Fault Injection Simulator — simulated in dev, boto3-ready."""

from __future__ import annotations

import logging
import uuid

from chaos_agent.config import get_settings
from chaos_agent.executors.base import AppliedResource, RollbackHandle
from chaos_agent.models import Fault

logger = logging.getLogger(__name__)


class AwsFisExecutor:
    def __init__(self, simulate: bool | None = None) -> None:
        self.simulate = simulate if simulate is not None else get_settings().simulate_execution

    async def apply(
        self,
        experiment_id: str,
        fault: Fault,
        namespace: str,
        max_replica_percent: float,
    ) -> RollbackHandle:
        template_id = fault.params.get("template_id", fault.type)
        resource_arn = fault.params.get("resource_arn", f"arn:aws:service:{fault.target or 'rds'}")
        experiment_name = f"chaos-{experiment_id[:12]}-{uuid.uuid4().hex[:6]}"

        if not self.simulate:
            try:
                import boto3

                client = boto3.client("fis")
                resp = client.start_experiment(
                    experimentTemplateId=template_id,
                    tags={"chaos_agent_experiment": experiment_id},
                )
                fis_id = resp.get("experiment", {}).get("id", experiment_name)
                logger.info("aws_fis_started", extra={"experiment_id": experiment_id, "fis_id": fis_id})
                return RollbackHandle(
                    experiment_id=experiment_id,
                    executor="aws_fis",
                    resources=[
                        AppliedResource(
                            api_version="fis/v1",
                            kind="Experiment",
                            namespace=namespace,
                            name=fis_id,
                        ),
                    ],
                    simulated=False,
                )
            except Exception as exc:
                logger.warning("aws_fis_fallback_simulate", extra={"error": str(exc)})
                self.simulate = True

        logger.info(
            "simulate_aws_fis_apply",
            extra={"experiment_id": experiment_id, "type": fault.type, "target": fault.target},
        )
        return RollbackHandle(
            experiment_id=experiment_id,
            executor="aws_fis",
            resources=[
                AppliedResource(
                    api_version="fis/v1",
                    kind="Experiment",
                    namespace=namespace,
                    name=experiment_name,
                ),
            ],
            simulated=True,
        )

    async def rollback(self, handle: RollbackHandle) -> None:
        if handle.simulated:
            logger.info("simulate_aws_fis_rollback", extra={"experiment_id": handle.experiment_id})
            return
        for resource in handle.resources:
            try:
                import boto3

                client = boto3.client("fis")
                client.stop_experiment(id=resource.name)
            except Exception as exc:
                logger.warning("aws_fis_rollback_failed", extra={"error": str(exc)})
