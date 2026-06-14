"""Observability collector — Prometheus, Grafana, Loki, Tempo, PagerDuty, GitHub."""

from __future__ import annotations

import httpx

from chaos_agent.collectors.loki.client import LokiClient
from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.collectors.tempo.client import TempoClient
from chaos_agent.config import get_settings
from chaos_agent.graph.types import ObservabilityTarget


class ObservabilityCollector:
    async def collect(self) -> list[ObservabilityTarget]:
        settings = get_settings()
        prom = PrometheusClient()
        loki = LokiClient()
        tempo = TempoClient()
        prom_ok = await prom.is_available()
        loki_ok = await loki.is_available()
        tempo_ok = await tempo.is_available()

        targets = [
            ObservabilityTarget(
                name="prometheus",
                type="prometheus",
                status="ok" if prom_ok else "gap",
                detail=None if prom_ok else "Unreachable — experiments run blind",
            ),
            ObservabilityTarget(
                name="loki",
                type="loki",
                status="ok" if loki_ok else "gap",
                detail=None if loki_ok else "Unreachable — log correlation disabled",
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
                status="ok" if tempo_ok else "gap",
                detail=None if tempo_ok else "Unreachable — trace correlation disabled",
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
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(url.rstrip("/") + "/api/health")
                return response.status_code < 500
        except Exception:
            return False
