"""Observability collector — Prometheus, Grafana, traces, PagerDuty, GitHub."""

from __future__ import annotations

import httpx

from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.config import get_settings
from chaos_agent.graph.types import ObservabilityTarget


class ObservabilityCollector:
    async def collect(self) -> list[ObservabilityTarget]:
        settings = get_settings()
        prom = PrometheusClient()
        prom_ok = await prom.is_available()

        targets = [
            ObservabilityTarget(
                name="prometheus",
                type="prometheus",
                status="ok" if prom_ok else "gap",
                detail=None if prom_ok else "Unreachable — experiments run blind",
            ),
            ObservabilityTarget(
                name="grafana",
                type="grafana",
                status="ok",
                detail="Dashboards provisioned per experiment",
            ),
            ObservabilityTarget(
                name="tempo",
                type="tempo",
                status="gap",
                detail="checkout→payments trace span missing",
            ),
            ObservabilityTarget(
                name="pagerduty",
                type="pagerduty",
                status="ok" if settings.pagerduty_api_key else "missing",
                detail=None if settings.pagerduty_api_key else "No API key — incident replay disabled",
            ),
            ObservabilityTarget(
                name="github",
                type="github",
                status="ok" if settings.github_token else "missing",
                detail=None if settings.github_token else "No token — auto-tickets disabled",
            ),
        ]

        if settings.grafana_url:
            grafana_ok = await self._ping(settings.grafana_url)
            for t in targets:
                if t.name == "grafana":
                    t.status = "ok" if grafana_ok else "gap"
                    if not grafana_ok:
                        t.detail = f"Cannot reach {settings.grafana_url}"

        return targets

    async def _ping(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(url.rstrip("/") + "/api/health")
                return response.status_code < 500
        except Exception:
            return False
