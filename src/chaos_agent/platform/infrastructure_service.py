"""Infrastructure rings view from live snapshot."""

from __future__ import annotations

from typing import Any

from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import SnapshotContext


async def get_infrastructure_rings(namespace: str = "staging") -> dict[str, Any]:
    builder = SnapshotBuilder(namespace)
    snapshot = await builder.build(SnapshotContext(namespace=namespace))

    rings: dict[str, list[dict[str, str]]] = {
        "k8s": [],
        "aws": [],
        "app": [],
        "deps": [],
        "observability": [],
    }

    for dep in snapshot.kubernetes.get("deployments", []):
        status = "ok" if dep.get("readiness_probe") and dep.get("priority_class") else "gap"
        rings["k8s"].append(
            {
                "name": dep.get("name", "unknown"),
                "detail": f"replicas={dep.get('replicas', '?')} · probes={'yes' if dep.get('readiness_probe') else 'no'}",
                "status": status,
            },
        )

    for rds in snapshot.aws.get("rds", []):
        rings["aws"].append(
            {
                "name": rds.get("id", "rds"),
                "detail": f"engine={rds.get('engine')} · multi_az={rds.get('multi_az', False)}",
                "status": "ok" if rds.get("multi_az") else "gap",
            },
        )
    for queue in snapshot.aws.get("sqs_queues", []):
        rings["aws"].append(
            {
                "name": queue.get("name", "sqs"),
                "detail": f"dlq={'yes' if queue.get('dlq') else 'no'}",
                "status": "ok" if queue.get("dlq") else "gap",
            },
        )

    for app in snapshot.applications:
        rings["app"].append(
            {
                "name": app.name,
                "detail": f"tier={app.tier} · retry={app.has_retry} · cb={app.has_circuit_breaker}",
                "status": "ok" if app.has_retry and app.has_circuit_breaker else "gap",
            },
        )

    for dep in snapshot.dependencies:
        rings["deps"].append(
            {
                "name": dep.name,
                "detail": f"{dep.type} · owner={dep.owner_service} · timeout={dep.has_timeout}",
                "status": "ok" if dep.has_timeout else "gap",
            },
        )

    for obs in snapshot.observability:
        rings["observability"].append(
            {
                "name": obs.name,
                "detail": obs.detail or obs.type,
                "status": obs.status,
            },
        )

    return {
        "rings": rings,
        "snapshot": snapshot.model_dump(mode="json"),
        "namespace": namespace,
    }
