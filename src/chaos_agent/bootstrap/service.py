"""Read-only bootstrap detectors — report install gaps from infra snapshot."""

from __future__ import annotations

from typing import Any

from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import SnapshotContext
from chaos_agent.platform.kube import kube_context_for_namespace


async def detect_bootstrap_status(namespace: str = "staging", *, cluster: str | None = None) -> dict[str, Any]:
    kube_context = cluster or kube_context_for_namespace(namespace)
    ctx = SnapshotContext(
        namespace=namespace,
        cluster=cluster or kube_context or "eks-staging",
        environment="production" if namespace == "production" else "staging",
    )
    builder = SnapshotBuilder(namespace, kube_context=kube_context)
    snapshot = await builder.build(ctx)
    k8s = snapshot.kubernetes or {}
    aws = snapshot.aws or {}

    deployments = k8s.get("deployments", [])
    missing_readiness = [d["name"] for d in deployments if not d.get("readiness_probe")]
    priority_classes = k8s.get("priority_classes", [])
    istio_enabled = bool(k8s.get("istio", {}).get("enabled"))
    rds_raw = aws.get("rds", [])
    if isinstance(rds_raw, list):
        rds_multi_az = any(isinstance(i, dict) and i.get("multi_az") for i in rds_raw)
    elif isinstance(rds_raw, dict):
        rds_multi_az = bool(rds_raw.get("multi_az"))
    else:
        rds_multi_az = False

    actions: list[dict[str, Any]] = [
        {
            "id": "istio-mesh",
            "action": "Install Istio service mesh",
            "scope": "k8s",
            "detail": "mTLS, retries, and traffic policies for blast containment",
            "status": "done" if istio_enabled else "available",
            "detected": istio_enabled,
            "requires_approval": True,
            "mutable": False,
        },
        {
            "id": "priority-class",
            "action": "Create workload-priority PriorityClass",
            "scope": "k8s",
            "detail": "Protect critical checkout/payments pods during node pressure",
            "status": "done" if priority_classes else "available",
            "detected": bool(priority_classes),
            "requires_approval": True,
            "mutable": False,
        },
        {
            "id": "readiness-probes",
            "action": "Add readiness probes",
            "scope": "k8s",
            "detail": f"Missing on: {', '.join(missing_readiness) or 'none'}",
            "status": "done" if not missing_readiness else "requires_approval",
            "detected": not missing_readiness,
            "requires_approval": True,
            "mutable": False,
        },
        {
            "id": "rds-multi-az",
            "action": "Enable RDS Multi-AZ",
            "scope": "aws",
            "detail": "payments-db failover for AZ loss",
            "status": "done" if rds_multi_az else "available",
            "detected": rds_multi_az,
            "requires_approval": True,
            "mutable": False,
        },
    ]

    return {
        "namespace": namespace,
        "cluster": ctx.cluster,
        "kube_context": kube_context,
        "live_data": k8s.get("source") == "live" or aws.get("source") == "live",
        "actions": actions,
        "summary": {
            "done": sum(1 for a in actions if a["status"] == "done"),
            "pending": sum(1 for a in actions if a["status"] != "done"),
        },
    }
