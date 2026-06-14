"""LLM-powered experiment composer."""

from __future__ import annotations

import json
from typing import Any, Optional

from chaos_agent.composer.prompts import COMPOSER_SYSTEM
from chaos_agent.config import get_settings
from chaos_agent.graph.provenance import snapshot_is_live, snapshot_provenance
from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import InfraSnapshot
from chaos_agent.llm.client import get_llm_client
from chaos_agent.models import ExperimentPlan, ExperimentSource


async def compose_with_llm(
    scenario: str,
    namespace: str = "staging",
    *,
    snapshot: Optional[InfraSnapshot] = None,
    prior_feedback: Optional[dict[str, Any]] = None,
    environment: str = "staging",
) -> Optional[tuple[ExperimentPlan, str]]:
    llm = get_llm_client()
    if not llm.available:
        return None

    settings = get_settings()
    builder = SnapshotBuilder(namespace)
    snap = snapshot or await builder.build()
    evidence = builder.evidence_lines(snap)[:12]
    sources = snapshot_provenance(snap)
    live = snapshot_is_live(snap)

    context = {
        "scenario": scenario,
        "namespace": namespace,
        "environment": environment,
        "live_data": live,
        "collection_sources": sources,
        "aws_fis_enabled": settings.aws_fis_enabled,
        "ebpf_enabled": settings.ebpf_enabled,
        "applications": [a.model_dump() for a in snap.applications],
        "dependencies": [d.model_dump() for d in snap.dependencies],
        "kubernetes": {
            "source": snap.kubernetes.get("source", "unknown"),
            "deployments": snap.kubernetes.get("deployments", [])[:8],
        },
        "aws": {
            "source": snap.aws.get("source", "unknown"),
            "rds": snap.aws.get("rds", [])[:4],
            "sqs_queues": snap.aws.get("sqs_queues", [])[:4],
        },
        "observability": [o.model_dump() for o in snap.observability],
        "graph_edges": [e.model_dump() for e in snap.graph_edges],
        "evidence_hints": evidence,
        "prior_feedback": prior_feedback,
    }

    if not live:
        context["grounding_warning"] = (
            "Snapshot uses seed/catalog data — verify targets against your real cluster before running."
        )

    data = await llm.complete_json(
        system=COMPOSER_SYSTEM,
        user=json.dumps(context, indent=2),
    )
    if not data:
        return None

    try:
        plan_data = _normalize_plan_payload(data, scenario, namespace, evidence, environment)
        plan = ExperimentPlan.model_validate(plan_data)
        plan.source = ExperimentSource.LLM
        summary = str(data.get("summary") or "LLM composer mapped scenario to faults using infra snapshot.")
        if prior_feedback:
            summary = f"Follow-up plan after {prior_feedback.get('experiment_id')}: {summary}"
        return plan, summary
    except Exception:
        return None


def _normalize_plan_payload(
    data: dict[str, Any],
    scenario: str,
    namespace: str,
    evidence: list[str],
    environment: str,
) -> dict[str, Any]:
    payload = dict(data)
    payload.pop("summary", None)
    payload.pop("revision_rationale", None)
    payload.setdefault("hypothesis", scenario)
    payload.setdefault("name", scenario[:48].lower().replace(" ", "-").strip("-") or "llm-scenario")
    payload.setdefault("infra_evidence", evidence[:6])
    payload.setdefault("source", ExperimentSource.LLM.value)

    blast = payload.setdefault("blast_radius", {})
    blast.setdefault("namespace", namespace)
    blast.setdefault("environment", environment)
    blast.setdefault("max_replicas_pct", 15.0)

    rollback = payload.setdefault("rollback", {})
    rollback.setdefault("type", "delete_chaos_crd")
    rollback.setdefault("ttl_seconds", 300)

    if not payload.get("targets"):
        payload["targets"] = [{"service": "checkout", "namespace": namespace}]
    if not payload.get("watch_metrics"):
        payload["watch_metrics"] = ["checkout_error_rate", "checkout_p99"]

    return payload
