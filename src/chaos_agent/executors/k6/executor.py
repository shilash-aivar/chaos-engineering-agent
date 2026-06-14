"""k6 load generator — simulated Job executor for experiments."""

from __future__ import annotations

import logging

from chaos_agent.config import get_settings
from chaos_agent.executors.base import RollbackHandle
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
        logger.info(
            "k6_load_started",
            extra={"experiment_id": experiment_id, "vus": vus, "duration": duration, "simulate": self.simulate},
        )
        return RollbackHandle(
            experiment_id=experiment_id,
            executor="k6",
            simulated=self.simulate,
        )

    async def rollback(self, handle: RollbackHandle) -> None:
        logger.info("k6_load_stopped", extra={"experiment_id": handle.experiment_id})
