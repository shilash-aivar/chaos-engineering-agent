"""Load prior experiment results for composer feedback loop."""

from __future__ import annotations

import json
from typing import Any, Optional

from chaos_agent.observability.types import FaultWindowEvidence
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository


async def load_feedback_context(
    experiment_id: str,
) -> Optional[dict[str, Any]]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            return None
        plan = repo.plan_from_row(row)
        events = await repo.get_events(experiment_id)
        evidence: dict[str, Any] = {}
        if row.evidence_json:
            ev = FaultWindowEvidence.model_validate_json(row.evidence_json)
            evidence = {
                "simulated": ev.simulated,
                "correlations": ev.correlations[:8],
                "ebpf_metrics": ev.ebpf_metrics,
                "metric_spikes": [
                    {"name": m.name, "delta_ratio": m.delta_ratio}
                    for m in ev.metrics
                    if m.delta_ratio and m.delta_ratio >= 1.5
                ],
            }
        return {
            "experiment_id": experiment_id,
            "name": row.name,
            "state": row.state,
            "slo_breached": bool(row.slo_breached),
            "hypothesis": plan.hypothesis,
            "faults": [f.model_dump() for f in plan.faults],
            "timeline": [
                {"event": e.event, "detail": e.detail}
                for e in events[-6:]
            ],
            "evidence": evidence,
        }


async def load_latest_feedback(namespace: str) -> Optional[dict[str, Any]]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get_latest_completed(namespace)
        if row is None:
            return None
    return await load_feedback_context(row.id)
