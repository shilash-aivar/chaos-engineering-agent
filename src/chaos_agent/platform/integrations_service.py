"""Integration connectivity status and probe APIs."""

from __future__ import annotations

import time

import httpx

from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.config import get_settings
from chaos_agent.integrations.pagerduty.client import PagerDutyClient


async def _ping(url: str) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if resp.status_code < 500:
                return True, f"HTTP {resp.status_code}"
            return False, f"HTTP {resp.status_code}"
    except Exception as exc:
        return False, str(exc)


async def get_integrations_status() -> list[dict]:
    settings = get_settings()
    prom = PrometheusClient()
    prom_ok = await prom.is_available()
    pd = PagerDutyClient()

    github_connected = bool(settings.github_token and settings.github_org and settings.github_repo)
    pagerduty_connected = pd.available
    slack_connected = bool(settings.slack_bot_token or settings.slack_webhook_url)

    grafana_ok, grafana_detail = await _ping(f"{settings.grafana_url.rstrip('/')}/api/health")
    loki_ok, loki_detail = await _ping(f"{settings.loki_url.rstrip('/')}/ready")
    tempo_ok, tempo_detail = await _ping(f"{settings.tempo_url.rstrip('/')}/ready")

    return [
        {
            "id": "prometheus",
            "name": "Prometheus",
            "type": "prometheus",
            "status": "connected" if prom_ok else "disconnected",
            "detail": settings.prometheus_url,
            "events": ["steady-state guard", "fault-window metrics", "SLO breach"],
            "configurable": False,
            "config_keys": ["PROMETHEUS_URL"],
        },
        {
            "id": "grafana",
            "name": "Grafana",
            "type": "grafana",
            "status": "connected" if grafana_ok else "disconnected",
            "detail": grafana_detail if not grafana_ok else settings.grafana_url,
            "events": ["dashboards", "alerting"],
            "configurable": False,
            "config_keys": ["GRAFANA_URL"],
        },
        {
            "id": "loki",
            "name": "Loki",
            "type": "loki",
            "status": "connected" if loki_ok else "disconnected",
            "detail": loki_detail if not loki_ok else settings.loki_url,
            "events": ["log correlation", "error patterns"],
            "configurable": False,
            "config_keys": ["LOKI_URL"],
        },
        {
            "id": "tempo",
            "name": "Tempo",
            "type": "tempo",
            "status": "connected" if tempo_ok else "disconnected",
            "detail": tempo_detail if not tempo_ok else settings.tempo_url,
            "events": ["trace correlation", "critical path"],
            "configurable": False,
            "config_keys": ["TEMPO_URL"],
        },
        {
            "id": "github",
            "name": "GitHub",
            "type": "github",
            "status": "connected" if github_connected else "disconnected",
            "detail": f"{settings.github_org}/{settings.github_repo}" if github_connected else "Set GITHUB_TOKEN",
            "events": ["remediation issues", "CI gate comments", "Blue PRs"],
            "configurable": True,
            "config_keys": ["CHAOS_AGENT_GITHUB_TOKEN", "CHAOS_AGENT_GITHUB_ORG", "CHAOS_AGENT_GITHUB_REPO"],
        },
        {
            "id": "pagerduty",
            "name": "PagerDuty",
            "type": "pagerduty",
            "status": "connected" if pagerduty_connected else "disconnected",
            "detail": "Incident API" if pagerduty_connected else "API key not set",
            "events": ["incident correlation", "on-call context"],
            "configurable": True,
            "config_keys": ["PAGERDUTY_API_KEY"],
        },
        {
            "id": "slack",
            "name": "Slack",
            "type": "slack",
            "status": "connected" if slack_connected else "disconnected",
            "detail": settings.slack_approval_channel if slack_connected else "Set SLACK_WEBHOOK_URL or BOT token",
            "events": ["awaiting_approval", "SLO breach", "campaign complete"],
            "configurable": True,
            "config_keys": ["CHAOS_AGENT_SLACK_WEBHOOK_URL", "CHAOS_AGENT_SLACK_BOT_TOKEN"],
        },
    ]


async def test_integration(integration_id: str) -> dict:
    settings = get_settings()
    started = time.perf_counter()

    if integration_id == "prometheus":
        ok = await PrometheusClient().is_available()
        message = "Prometheus query API reachable" if ok else "Prometheus unreachable"
    elif integration_id == "grafana":
        ok, message = await _ping(f"{settings.grafana_url.rstrip('/')}/api/health")
    elif integration_id == "loki":
        ok, message = await _ping(f"{settings.loki_url.rstrip('/')}/ready")
    elif integration_id == "tempo":
        ok, message = await _ping(f"{settings.tempo_url.rstrip('/')}/ready")
    elif integration_id == "github":
        ok = bool(settings.github_token and settings.github_org and settings.github_repo)
        if ok:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"https://api.github.com/repos/{settings.github_org}/{settings.github_repo}",
                        headers={"Authorization": f"Bearer {settings.github_token}"},
                    )
                ok = resp.status_code == 200
                message = "GitHub repo accessible" if ok else f"GitHub API HTTP {resp.status_code}"
            except Exception as exc:
                ok = False
                message = str(exc)
        else:
            message = "GITHUB_TOKEN, GITHUB_ORG, and GITHUB_REPO required"
    elif integration_id == "pagerduty":
        pd = PagerDutyClient()
        ok = pd.available
        message = "PagerDuty API key configured" if ok else "PAGERDUTY_API_KEY not set"
    elif integration_id == "slack":
        ok = bool(settings.slack_bot_token or settings.slack_webhook_url)
        if ok and settings.slack_webhook_url:
            try:
                from chaos_agent.integrations.slack.client import SlackClient

                slack = SlackClient()
                ok = slack.available
                message = "Slack webhook configured" if ok else "Slack client unavailable"
            except Exception as exc:
                ok = False
                message = str(exc)
        elif ok:
            message = "Slack bot token configured"
        else:
            message = "SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN required"
    else:
        return {"ok": False, "message": f"Unknown integration: {integration_id}", "latency_ms": 0}

    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return {"ok": ok, "message": message, "latency_ms": latency_ms, "integration_id": integration_id}
