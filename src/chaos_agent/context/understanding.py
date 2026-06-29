"""Build human-readable understanding summary from declared + observed context."""

from __future__ import annotations

from typing import Any

from chaos_agent.context.types import ContextSnapshot, DeclaredContext
from chaos_agent.graph.types import InfraSnapshot


def build_understanding(declared: DeclaredContext, snapshot: InfraSnapshot) -> dict[str, Any]:
    """Summarize what the agent read and understood from declared vs observed sources."""
    tf_types: dict[str, int] = {}
    for res in declared.terraform_resources:
        tf_types[res.type] = tf_types.get(res.type, 0) + 1

    doc_claims: list[str] = []
    for doc in declared.documents:
        doc_claims.extend(doc.claims)

    declared_services = {res.name.replace("_", "-") for res in declared.terraform_resources}
    declared_services.update(
        hint.split(":")[-1].strip().split("=")[-1].strip()
        for hint in declared.manifest_hints
        if "resource name=" in hint
    )

    live_apps = {a.name for a in snapshot.applications}
    live_deps = {d.name for d in snapshot.dependencies}
    live_rds = {r.get("id", "") for r in snapshot.aws.get("rds", []) if isinstance(r, dict)}

    matched = declared_services & (live_apps | live_deps | live_rds)
    undeclared_live = (live_apps | live_deps | live_rds) - declared_services
    declared_only = declared_services - live_apps - live_deps - live_rds

    return {
        "declared": {
            "terraform_resource_types": tf_types,
            "terraform_file_count": len(declared.terraform_sources),
            "document_count": len(declared.documents),
            "manifest_file_count": len(declared.manifest_sources),
            "code_file_count": len(declared.code_sources),
            "claims": doc_claims,
            "code_hints": declared.code_hints[:20],
            "manifest_hints": declared.manifest_hints[:20],
        },
        "observed": {
            "applications": [a.name for a in snapshot.applications],
            "dependencies": [d.name for d in snapshot.dependencies],
            "rds_instances": list(live_rds),
            "sqs_queues": [
                q.get("name", "unknown") for q in snapshot.aws.get("sqs_queues", []) if isinstance(q, dict)
            ],
            "load_balancers": [
                lb.get("name", "unknown") for lb in snapshot.aws.get("load_balancers", []) if isinstance(lb, dict)
            ],
            "elasticache": [
                c.get("name", "unknown") for c in snapshot.aws.get("elasticache", []) if isinstance(c, dict)
            ],
            "aws_source": snapshot.aws.get("source"),
            "aws_region": snapshot.aws.get("region"),
            "aws_account_id": snapshot.aws.get("account_id"),
            "observability": [
                {"name": o.name, "status": o.status} for o in snapshot.observability
            ],
            "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else None,
        },
        "alignment": {
            "matched_resources": sorted(matched),
            "declared_not_observed": sorted(declared_only),
            "observed_not_declared": sorted(undeclared_live),
        },
    }


def understanding_from_snapshot(context: ContextSnapshot, infra: InfraSnapshot) -> dict[str, Any]:
    return build_understanding(context.declared, infra)
