"""LLM-powered experiment composer."""

from __future__ import annotations

import json
from typing import Any, Optional

from chaos_agent.composer.prompts import COMPOSER_SYSTEM
from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import InfraSnapshot
from chaos_agent.llm.client import get_llm_client
from chaos_agent.models import ExperimentPlan, ExperimentSource


async def compose_with_llm(
    scenario: str,
    namespace: str = "staging",
    *,
    snapshot: Optional[InfraSnapshot] = None,
) -> Optional[tuple[ExperimentPlan, str]]:
    llm = get_llm_client()
    if not llm.available:
        return None

    builder = SnapshotBuilder(namespace)
    snap = snapshot or await builder.build()
    evidence = builder.evidence_lines(snap)[:12]

    context = {
        "scenario": scenario,
        "namespace": namespace,
        "applications": [a.model_dump() for a in snap.applications],
        "dependencies": [d.model_dump() for d in snap.dependencies],
        "observability": [o.model_dump() for o in snap.observability],
        "graph_edges": [e.model_dump() for e in snap.graph_edges],
        "evidence_hints": evidence,
    }

    data = await llm.complete_json(
        system=COMPOSER_SYSTEM,
        user=json.dumps(context, indent=2),
    )
    if not data:
        return None

    try:
        plan_data = _normalize_plan_payload(data, scenario, namespace, evidence)
        plan = ExperimentPlan.model_validate(plan_data)
        plan.source = ExperimentSource.LLM
        summary = str(data.get("summary") or "LLM composer mapped scenario to faults using live snapshot.")
        return plan, summary
    except Exception:
        return None


def _normalize_plan_payload(
    data: dict[str, Any],
    scenario: str,
    namespace: str,
    evidence: list[str],
) -> dict[str, Any]:
    payload = dict(data)
    payload.pop("summary", None)
    payload.setdefault("hypothesis", scenario)
    payload.setdefault("name", scenario[:48].lower().replace(" ", "-").strip("-") or "llm-scenario")
    payload.setdefault("infra_evidence", evidence[:6])
    payload.setdefault("source", ExperimentSource.LLM.value)

    blast = payload.setdefault("blast_radius", {})
    blast.setdefault("namespace", namespace)
    blast.setdefault("environment", "staging")
    blast.setdefault("max_replicas_pct", 30.0)

    rollback = payload.setdefault("rollback", {})
    rollback.setdefault("type", "delete_chaos_crd")
    rollback.setdefault("ttl_seconds", 300)

    if not payload.get("targets"):
        payload["targets"] = [{"service": "checkout", "namespace": namespace}]
    if not payload.get("watch_metrics"):
        payload["watch_metrics"] = ["checkout_error_rate", "checkout_p99"]

    return payload
