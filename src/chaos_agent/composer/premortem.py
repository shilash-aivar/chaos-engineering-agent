"""Pre-mortem generation — twin-grounded risk narrative before inject."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import InfraSnapshot
from chaos_agent.llm.client import get_llm_client
from chaos_agent.models import ExperimentPlan
from chaos_agent.platform.twin_service import simulate_blast

PREMORTEM_SYSTEM = """You are the Composer agent writing a pre-mortem before a chaos experiment.
Given an ExperimentPlan and blast simulation, write a concise pre-mortem (3-5 bullet risks + mitigations).

Respond with ONLY JSON:
{
  "summary": "one sentence overall risk",
  "risks": ["risk 1", "risk 2"],
  "mitigations": ["existing control 1", "rollback plan"],
  "go_no_go": "go|caution|no-go",
  "narrative": "2-3 sentence operator briefing"
}"""


async def generate_pre_mortem(
    plan: ExperimentPlan,
    *,
    snapshot: Optional[InfraSnapshot] = None,
    namespace: Optional[str] = None,
) -> dict[str, Any]:
    ns = namespace or plan.blast_radius.namespace
    builder = SnapshotBuilder(ns)
    snap = snapshot or await builder.build()
    fault_target = plan.faults[0].target if plan.faults else "checkout"
    twin = simulate_blast(snap, fault_target=fault_target or "checkout")

    llm = get_llm_client()
    if llm.available:
        import json

        payload = {
            "plan": plan.model_dump(),
            "twin": {
                "paths_analyzed": twin["paths_analyzed"],
                "failure_probability_pct": twin["failure_probability_pct"],
                "predicted_cascade": twin["predicted_cascade"],
            },
            "evidence": plan.infra_evidence[:8],
        }
        data = await llm.complete_json(system=PREMORTEM_SYSTEM, user=json.dumps(payload, indent=2))
        if data:
            return {**data, "twin_preview": twin}

    return {
        "summary": f"Inject {plan.faults[0].type if plan.faults else 'fault'} on {fault_target}",
        "risks": [
            f"Predicted cascade: {twin['predicted_cascade']}",
            f"Failure probability ~{twin['failure_probability_pct']}%",
        ],
        "mitigations": [
            f"Rollback: {plan.rollback.type} TTL {plan.rollback.ttl_seconds}s",
            f"Watch metrics: {', '.join(plan.watch_metrics[:3])}",
        ],
        "go_no_go": "caution" if twin["failure_probability_pct"] > 15 else "go",
        "narrative": (
            f"Twin analyzed {twin['paths_analyzed']} paths. "
            f"Steady-state guard armed on {len(plan.watch_metrics)} metrics."
        ),
        "twin_preview": twin,
    }
