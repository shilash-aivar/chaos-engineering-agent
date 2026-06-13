"""Fault executor interfaces."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from chaos_agent.models import Fault


@dataclass
class AppliedResource:
    api_version: str
    kind: str
    namespace: str
    name: str


@dataclass
class RollbackHandle:
    experiment_id: str
    executor: str = "chaos_mesh"
    resources: list[AppliedResource] = field(default_factory=list)
    simulated: bool = False


class FaultExecutor(Protocol):
    async def apply(
        self,
        experiment_id: str,
        fault: Fault,
        namespace: str,
        max_replica_percent: float,
    ) -> RollbackHandle: ...

    async def rollback(self, handle: RollbackHandle) -> None: ...


def fault_label_selector(target: str) -> dict[str, str]:
    """Map service name to common K8s label selectors."""
    return {"app": target}
