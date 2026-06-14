"""Load test scenario execution."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)
from chaos_agent.platform.load_tests_data import PAIRINGS, SCENARIOS, get_load_tests_catalog


def find_scenario(scenario_id: str) -> Optional[dict[str, Any]]:
    return next((s for s in SCENARIOS if s["id"] == scenario_id), None)


def find_pairing(pairing_id: str) -> Optional[dict[str, Any]]:
    return next((p for p in PAIRINGS if p["id"] == pairing_id), None)


def scenario_to_plan(
    scenario_id: str,
    *,
    namespace: str = "staging",
    include_fault: bool = True,
    pairing_id: Optional[str] = None,
) -> ExperimentPlan:
    scenario = find_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    faults: list[Fault] = [
        Fault(
            executor=FaultExecutor.K6,
            type=scenario["type"],
            target=scenario["target"],
            params={"vus": scenario["vus"], "duration": scenario["duration"]},
        ),
    ]

    if include_fault:
        pairing = find_pairing(pairing_id) if pairing_id else None
        if pairing is None:
            pairing = next((p for p in PAIRINGS if p["load_type"] == scenario["type"]), None)
        if pairing:
            fault_parts = pairing["fault"].split("/", 1)
            executor_name = fault_parts[0]
            rest = fault_parts[1] if len(fault_parts) > 1 else ""
            fault_type, _, target = rest.partition(" → ")
            executor = FaultExecutor(executor_name)
            faults.append(
                Fault(
                    executor=executor,
                    type=fault_type.strip() or "pod_kill",
                    target=target.strip() or scenario["target"],
                ),
            )

    metrics = [
        f"{scenario['target']}_error_rate",
        f"{scenario['target']}_request_rate",
        f"{scenario['target']}_latency_p99",
    ]

    return ExperimentPlan(
        name=scenario["name"],
        hypothesis=scenario["hypothesis"],
        targets=[Target(service=scenario["target"], namespace=namespace)],
        faults=faults,
        blast_radius=BlastRadius(namespace=namespace, max_replicas_pct=15),
        watch_metrics=metrics,
        rollback=RollbackSpec(type="delete_chaos_crd", ttl_seconds=300),
        source=ExperimentSource.HUMAN,
        load={"scenario_id": scenario_id, "vus": scenario["vus"], "duration": scenario["duration"]},
    )


def get_catalog() -> dict[str, Any]:
    return get_load_tests_catalog()
