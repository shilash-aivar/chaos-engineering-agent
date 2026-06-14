"""Rule-based scenario composer — uses infra snapshot when available."""

from __future__ import annotations

from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)


async def compose_from_scenario(scenario: str, namespace: str = "staging") -> tuple[ExperimentPlan, str]:
    scenario_lower = scenario.lower()
    name = scenario[:48].lower().replace(" ", "-").strip("-") or "custom-scenario"

    builder = SnapshotBuilder(namespace)
    snapshot = await builder.build()
    evidence = builder.evidence_lines(snapshot)[:6]

    faults: list[Fault] = []
    targets = [Target(service="checkout", namespace=namespace)]
    watch_metrics = ["checkout_error_rate", "checkout_p99"]

    if "pod" in scenario_lower and "kill" in scenario_lower:
        service = "payments-api" if "payment" in scenario_lower else "checkout"
        targets = [Target(service=service, namespace=namespace)]
        faults.append(Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target=service))

    if "latency" in scenario_lower or "slow" in scenario_lower:
        target = "inventory-api" if "inventory" in scenario_lower else "payments-api"
        faults.append(
            Fault(
                executor=FaultExecutor.CHAOS_MESH,
                type="network_latency",
                target=target,
                params={"latency_ms": 500},
            ),
        )

    if any(k in scenario_lower for k in ("db", "database", "postgres", "rds", "blackhole", "connectivity")):
        faults.append(
            Fault(
                executor=FaultExecutor.TOXIPROXY,
                type="dependency_blackhole",
                target="payments-db",
                params={"duration": "60s"},
            ),
        )
        watch_metrics.append("db_connection_errors")

    if any(k in scenario_lower for k in ("redis", "cache")):
        faults.append(
            Fault(
                executor=FaultExecutor.TOXIPROXY,
                type="timeout",
                target="session-cache",
            ),
        )

    if any(k in scenario_lower for k in ("stripe", "third-party", "auth0", "auth")):
        dep = "stripe-api" if "stripe" in scenario_lower else "auth0"
        faults.append(
            Fault(
                executor=FaultExecutor.TOXIPROXY,
                type="latency",
                target=dep,
                params={"latency_ms": 3000},
            ),
        )

    if any(k in scenario_lower for k in ("kafka", "queue")):
        faults.append(
            Fault(
                executor=FaultExecutor.TOXIPROXY,
                type="timeout",
                target="order-events",
            ),
        )

    if not faults:
        faults.append(Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="checkout"))
        evidence.append("default: pod_kill on checkout")

    if not evidence:
        evidence = ["Infra snapshot loaded — no critical gaps in evidence preview"]

    max_replicas = 20.0 if any(f.type == "pod_kill" for f in faults) else 30.0
    plan = ExperimentPlan(
        name=name,
        hypothesis=scenario,
        source=ExperimentSource.HYBRID,
        targets=targets,
        faults=faults,
        infra_evidence=evidence,
        blast_radius=BlastRadius(namespace=namespace, environment="staging", max_replicas_pct=max_replicas),
        watch_metrics=watch_metrics,
        rollback=RollbackSpec(type="delete_chaos_crd", ttl_seconds=300),
    )

    layers = []
    if any(f.executor == FaultExecutor.CHAOS_MESH for f in faults):
        layers.append("K8s")
    if any(f.executor == FaultExecutor.TOXIPROXY for f in faults):
        layers.append("deps")
    summary = (
        f"Composer mapped scenario across {' + '.join(layers) or 'infra'} using live snapshot. "
        f"Evidence from {len(snapshot.applications)} apps, {len(snapshot.dependencies)} deps, "
        f"{len(snapshot.observability)} observability targets."
    )
    return plan, summary
