"""Celery tasks — offload long experiment runs."""

from __future__ import annotations

import asyncio
import logging

from chaos_agent.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro) -> None:
    asyncio.run(coro)


@celery_app.task(name="chaos_agent.run_experiment", bind=True, max_retries=0)
def run_experiment_task(self, experiment_id: str) -> dict:
    """Start experiment orchestration in a worker process."""
    try:
        from chaos_agent.orchestrator.engine import get_engine

        _run_async(get_engine().start(experiment_id))
        return {"experiment_id": experiment_id, "status": "started"}
    except Exception as exc:
        logger.exception("celery_experiment_failed", extra={"experiment_id": experiment_id})
        return {"experiment_id": experiment_id, "status": "failed", "error": str(exc)}


def dispatch_experiment(experiment_id: str) -> tuple[bool, str]:
    """Enqueue experiment if Celery broker is configured; returns (async, detail)."""
    from chaos_agent.config import get_settings

    settings = get_settings()
    if not settings.use_celery:
        return False, "inline"

    try:
        run_experiment_task.delay(experiment_id)
        return True, "celery"
    except Exception as exc:
        logger.warning("celery_dispatch_failed", extra={"error": str(exc)})
        return False, f"inline_fallback:{exc}"
