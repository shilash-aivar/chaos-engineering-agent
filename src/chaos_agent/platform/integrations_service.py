"""Integration connectivity status."""

from __future__ import annotations

import httpx

from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.config import get_settings
from chaos_agent.integrations.pagerduty.client import PagerDutyClient
from chaos_agent.integrations.pagerduty.client import PagerDutyClient


async def _ping(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            return resp.status_code < 500
    except Exception:
        return False


async def get_integrations_status() -> list[dict]:
    settings = get_settings()
    prom = PrometheusClient()
    prom_ok = await prom.is_available()
    pd = PagerDutyClient()

    github_connected = bool(settings.github_token and settings.github_org and settings.github_repo)
    pagerduty_connected = pd.available
    slack_connected = bool(settings.slack_bot_token or settings.slack_webhook_url)

    grafana_ok = await _ping(f"{settings.grafana_url.rstrip('/')}/api/health")
    loki_ok = await _ping(f"{settings.loki_url.rstrip('/')}/ready")
    tempo_ok = await _ping(f"{settings.tempo_url.rstrip('/')}/ready")

    return [
        {
            "id": "prometheus",
            "name": "Prometheus",
            "type": "prometheus",
            "status": "connected" if prom_ok else "disconnected",
            "detail": settings.prometheus_url,
            "events": ["steady-state guard", "fault-window metrics", "SLO breach"],
        },
        {
            "id": "grafana",
            "name": "Grafana",
            "type": "grafana",
            "status": "connected" if grafana_ok else "disconnected",
            "detail": settings.grafana_url,
            "events": ["dashboards", "alerting"],
        },
        {
            "id": "loki",
            "name": "Loki",
            "type": "loki",
            "status": "connected" if loki_ok else "disconnected",
            "detail": settings.loki_url,
            "events": ["log correlation", "error patterns"],
        },
        {
            "id": "tempo",
            "name": "Tempo",
            "type": "tempo",
            "status": "connected" if tempo_ok else "disconnected",
            "detail": settings.tempo_url,
            "events": ["trace correlation", "critical path"],
        },
        {
            "id": "github",
            "name": "GitHub",
            "type": "github",
            "status": "connected" if github_connected else "disconnected",
            "detail": f"{settings.github_org}/{settings.github_repo}" if github_connected else "Set GITHUB_TOKEN",
            "events": ["remediation issues", "CI gate comments", "Blue PRs"],
        },
        {
            "id": "pagerduty",
            "name": "PagerDuty",
            "type": "pagerduty",
            "status": "connected" if pagerduty_connected else "disconnected",
            "detail": "Incident API" if pagerduty_connected else "API key not set",
            "events": ["incident correlation", "on-call context"],
        },
        {
            "id": "slack",
            "name": "Slack",
            "type": "slack",
            "status": "connected" if slack_connected else "disconnected",
            "detail": settings.slack_approval_channel if slack_connected else "Set SLACK_WEBHOOK_URL or BOT token",
            "events": ["awaiting_approval", "SLO breach", "campaign complete"],
        },
    ]
