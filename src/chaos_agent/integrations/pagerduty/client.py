"""PagerDuty — incident context for observability correlation."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from chaos_agent.config import get_settings

logger = logging.getLogger(__name__)


class PagerDutyClient:
    def __init__(self) -> None:
        self.api_key = get_settings().pagerduty_api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def list_recent_incidents(self, *, limit: int = 5) -> list[dict[str, Any]]:
        if not self.available:
            return []

        headers = {
            "Authorization": f"Token token={self.api_key}",
            "Accept": "application/vnd.pagerduty+json;version=2",
        }
        params = {"limit": limit, "sort_by": "created_at:desc", "statuses[]": ["triggered", "acknowledged"]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.pagerduty.com/incidents",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("pagerduty_fetch_failed", extra={"error": str(exc)})
            return []

        out = []
        for inc in data.get("incidents", []):
            out.append(
                {
                    "id": inc.get("id"),
                    "title": inc.get("title"),
                    "status": inc.get("status"),
                    "urgency": inc.get("urgency"),
                    "service": (inc.get("service") or {}).get("summary"),
                    "created_at": inc.get("created_at"),
                },
            )
        return out

    async def correlate_experiment(self, experiment_id: str, service: Optional[str] = None) -> dict[str, Any]:
        incidents = await self.list_recent_incidents()
        if service:
            incidents = [i for i in incidents if service.lower() in (i.get("service") or "").lower()]
        return {
            "experiment_id": experiment_id,
            "incidents": incidents,
            "correlated": len(incidents) > 0,
        }
