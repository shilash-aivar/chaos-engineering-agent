"""Capture fault-window evidence for an experiment (orchestrator + API backfill)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from chaos_agent.config import get_settings
from chaos_agent.models import ExperimentState
from chaos_agent.observability.correlator import ObservabilityCorrelator, utcnow
from chaos_agent.observability.types import FaultWindowEvidence
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

_correlator = ObservabilityCorrelator()


async def capture_experiment_evidence(
    experiment_id: str,
    *,
    force_simulate: Optional[bool] = None,
) -> FaultWindowEvidence:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")

        if row.state not in (ExperimentState.COMPLETE.value, ExperimentState.FAILED.value):
            raise HTTPException(
                status_code=409,
                detail=f"Evidence available after experiment completes (current state: {row.state})",
            )

        plan = repo.plan_from_row(row)
        baseline: dict[str, float] = {}
        if row.baseline_json:
            baseline = json.loads(row.baseline_json)
        if not baseline:
            baseline = {m: 0.01 if "error" in m else 0.2 for m in plan.watch_metrics}

        events = await repo.get_events(experiment_id)
        window_start = row.created_at
        for event in events:
            if event.event == "Fault injected":
                window_start = event.created_at
                break

        window_end = row.completed_at or utcnow()
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)

        simulate = force_simulate
        if simulate is None:
            simulate = get_settings().simulate_execution

        evidence = await _correlator.build_evidence(
            experiment_id,
            plan,
            baseline=baseline,
            window_start=window_start,
            window_end=window_end,
            slo_breached=bool(row.slo_breached),
            force_simulate=simulate,
        )
        await repo.set_evidence(experiment_id, evidence)
        return evidence
