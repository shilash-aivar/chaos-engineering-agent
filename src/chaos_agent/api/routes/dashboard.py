from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from chaos_agent.red_blue import campaign as rb
from chaos_agent.models import ExperimentState
from chaos_agent.posture.scanner import PostureScanner
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()


@router.get("/stats")
async def get_stats(namespace: Optional[str] = None) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        rows = await repo.list_all(namespace=namespace)

    running = sum(1 for r in rows if r.state == ExperimentState.RUNNING.value)
    complete = [r for r in rows if r.state == ExperimentState.COMPLETE.value]
    avg_score = 0
    if complete:
        scored = [r for r in complete if r.red_score is not None]
        if scored:
            avg_score = round(sum(r.red_score or 0 for r in scored) / len(scored))

    ns = namespace or "staging"
    posture = await PostureScanner(ns).scan()
    campaigns = await rb.list_campaigns()
    if namespace:
        campaigns = [c for c in campaigns if c.get("namespace") == namespace]
    active_campaign = next((c for c in campaigns if c.get("state") == "active"), None)
    return {
        "experiments_total": len(rows),
        "experiments_running": running,
        "avg_resilience_score": avg_score,
        "posture_gaps": len(posture["gaps"]),
        "red_blue_campaigns": len(campaigns),
        "active_campaign": active_campaign,
        "last_experiment_at": rows[0].created_at.isoformat() if rows else None,
        "namespace": namespace,
    }
