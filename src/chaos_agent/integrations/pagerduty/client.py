"""PagerDuty integration — incident replay for scenario generation."""

from __future__ import annotations

from typing import Any

from chaos_agent.config import get_settings


class PagerDutyClient:
    def __init__(self) -> None:
        self.api_key = get_settings().pagerduty_api_key

    async def list_recent_incidents(self, limit: int = 5) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        # Phase 2: GET https://api.pagerduty.com/incidents
        return [
            {
                "id": "PD-001",
                "title": "Redis eviction caused checkout errors",
                "service": "checkout",
                "suggested_scenario": "cache eviction + traffic spike on checkout",
            },
        ]
