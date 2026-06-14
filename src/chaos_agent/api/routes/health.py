"""Health and readiness probes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from sqlalchemy import text

from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.config import get_settings
from chaos_agent.observability.correlator import ObservabilityCorrelator
from chaos_agent.storage.database import get_session_factory

router = APIRouter()


async def _check_db() -> dict:
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "degraded", "detail": str(exc)}


async def _check_collectors() -> dict:
    prom = PrometheusClient()
    correlator = ObservabilityCorrelator()
    prom_ok, obs = await asyncio.gather(prom.is_available(), correlator.backend_status())
    return {
        "prometheus": "ok" if prom_ok else "gap",
        "loki": obs.loki,
        "tempo": obs.tempo,
    }


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    db, collectors = await asyncio.gather(_check_db(), _check_collectors())
    components = {
        "database": db["status"],
        "prometheus": collectors["prometheus"],
        "loki": collectors["loki"],
        "tempo": collectors["tempo"],
    }
    degraded = any(v in ("degraded", "gap") for v in components.values())
    return {
        "status": "degraded" if degraded else "ok",
        "version": "0.1.0",
        "environment": settings.env,
        "components": components,
        "auth_required": bool(settings.api_key),
    }
