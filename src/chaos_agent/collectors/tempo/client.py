"""Tempo HTTP client — trace search."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from chaos_agent.config import get_settings

logger = logging.getLogger(__name__)


class TempoClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or get_settings().tempo_url).rstrip("/")

    async def search(
        self,
        traceql: str,
        start: datetime,
        end: datetime,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search traces via Tempo TraceQL / search API."""
        url = f"{self.base_url}/api/search"
        params = {
            "q": traceql,
            "start": str(int(start.timestamp())),
            "end": str(int(end.timestamp())),
            "limit": str(limit),
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except Exception as exc:
            logger.warning("tempo_search_failed", extra={"error": str(exc), "query": traceql})
            return []

        traces = payload.get("traces") or []
        if isinstance(traces, list):
            return traces
        return []

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/ready")
                return response.status_code == 200
        except Exception:
            return False
