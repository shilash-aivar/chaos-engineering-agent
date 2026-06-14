"""Run Red attacks as real chaos experiments."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional

from chaos_agent.composer.validators.safety import validate_plan
from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    ExperimentState,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)
from chaos_agent.orchestrator.engine import get_engine
from chaos_agent.security.types import RedAttack
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

_FAULT_MAP = {
    "pod_kill": (FaultExecutor.CHAOS_MESH, "pod_kill"),
    "network_latency": (FaultExecutor.CHAOS_MESH, "network_latency"),
    "dependency_blackhole": (FaultExecutor.TOXIPROXY, "dependency_blackhole"),
    "timeout": (FaultExecutor.TOXIPROXY, "timeout"),
    "latency": (FaultExecutor.TOXIPROXY, "latency"),
}


def attack_to_plan(attack: RedAttack, namespace: str = "staging") -> ExperimentPlan:
    faults: list[Fault] = []
    for raw in attack.faults:
        ftype = raw.get("type", attack.technique)
        target = raw.get("target", attack.service)
        executor, mapped_type = _FAULT_MAP.get(ftype, (FaultExecutor.CHAOS_MESH, ftype))
        params: dict[str, Any] = {}
        if mapped_type == "network_latency":
            params["latency_ms"] = 500
        if mapped_type == "dependency_blackhole":
            params["duration"] = "60s"
        faults.append(Fault(executor=executor, type=mapped_type, target=target, params=params))

    if not faults:
        executor, mapped_type = _FAULT_MAP.get(attack.technique, (FaultExecutor.CHAOS_MESH, attack.technique))
        faults.append(Fault(executor=executor, type=mapped_type, target=attack.service))

    slug = f"red-{attack.technique}-{uuid.uuid4().hex[:6]}"
    return ExperimentPlan(
        name=slug,
        hypothesis=f"Red round: {attack.title}",
        source=ExperimentSource.RED_AGENT,
        targets=[Target(service=attack.service, namespace=namespace)],
        faults=faults,
        infra_evidence=[attack.transcript[:200]],
        blast_radius=BlastRadius(namespace=namespace, environment="staging"),
        watch_metrics=["checkout_error_rate", "checkout_p99"],
        rollback=RollbackSpec(type="delete_chaos_crd", ttl_seconds=300),
    )


async def inject_attack(
    attack: RedAttack,
    namespace: str = "staging",
    *,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    plan = attack_to_plan(attack, namespace)
    validate_plan(plan)

    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.create(plan)
        exp_id = row.id

    await get_engine().start(exp_id)

    elapsed = 0
    interval = 2
    final_state = ExperimentState.PENDING.value
    slo_breached = False

    while elapsed < timeout_seconds:
        await asyncio.sleep(interval)
        elapsed += interval
        async with factory() as session:
            repo = ExperimentRepository(session)
            row = await repo.get(exp_id)
            if row is None:
                break
            final_state = row.state
            slo_breached = bool(row.slo_breached)
            if final_state in (
                ExperimentState.COMPLETE.value,
                ExperimentState.FAILED.value,
            ):
                break

    return {
        "experiment_id": exp_id,
        "state": final_state,
        "slo_breached": slo_breached,
        "injected": final_state == ExperimentState.COMPLETE.value,
    }
