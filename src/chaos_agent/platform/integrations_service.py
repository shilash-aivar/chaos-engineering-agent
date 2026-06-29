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


async def _check_kubernetes() -> tuple[bool, str]:
    def _probe() -> tuple[bool, str]:
        try:
            from kubernetes import client

            from chaos_agent.platform.kube import load_kubernetes_config

            load_kubernetes_config()
            version = client.VersionApi().get_code()
            return True, f"Kubernetes {version.git_version}"
        except Exception as exc:
            return False, str(exc)

    import asyncio

    try:
        return await asyncio.wait_for(asyncio.to_thread(_probe), timeout=4)
    except Exception as exc:
        return False, str(exc)


async def _check_aws() -> tuple[bool, str]:
    def _probe() -> tuple[bool, str]:
        try:
            from botocore.config import Config

            from chaos_agent.platform.aws import boto_session, resolve_aws_config

            _, region = resolve_aws_config()
            cfg = Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 1})
            sts = boto_session().client("sts", config=cfg)
            ident = sts.get_caller_identity()
            return True, f"Account {ident.get('Account', 'unknown')} · {region}"
        except Exception as exc:
            return False, str(exc)

    import asyncio

    try:
        return await asyncio.wait_for(asyncio.to_thread(_probe), timeout=4)
    except Exception as exc:
        return False, str(exc)


async def get_integrations_status() -> list[dict]:
    from chaos_agent.platform.connector_store import apply_connectors_to_settings

    apply_connectors_to_settings()
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
    k8s_ok, k8s_detail = await _check_kubernetes()
    aws_ok, aws_detail = await _check_aws()

    return [
        {
            "id": "kubernetes",
            "name": "Kubernetes",
            "type": "kubernetes",
            "status": "connected" if k8s_ok else "disconnected",
            "detail": k8s_detail if k8s_ok else f"{k8s_detail} — using simulation/seed",
            "events": ["snapshot", "Chaos Mesh faults", "k6 jobs", "rollback"],
            "configurable": True,
            "config_keys": ["kube_context", "kubeconfig_path"],
        },
        {
            "id": "aws",
            "name": "AWS",
            "type": "aws",
            "status": "connected" if aws_ok else "disconnected",
            "detail": aws_detail if aws_ok else f"{aws_detail} — using seed",
            "events": ["RDS", "ELB", "SQS", "ElastiCache posture"],
            "configurable": True,
            "config_keys": ["profile", "region"],
        },
        {
            "id": "prometheus",
            "name": "Prometheus",
            "type": "prometheus",
            "status": "connected" if prom_ok else "disconnected",
            "detail": settings.prometheus_url,
            "events": ["steady-state guard", "fault-window metrics", "SLO breach"],
            "configurable": True,
            "config_keys": ["url"],
        },
        {
            "id": "grafana",
            "name": "Grafana",
            "type": "grafana",
            "status": "connected" if grafana_ok else "disconnected",
            "detail": grafana_detail if not grafana_ok else settings.grafana_url,
            "events": ["dashboards", "alerting"],
            "configurable": True,
            "config_keys": ["url"],
        },
        {
            "id": "loki",
            "name": "Loki",
            "type": "loki",
            "status": "connected" if loki_ok else "disconnected",
            "detail": loki_detail if not loki_ok else settings.loki_url,
            "events": ["log correlation", "error patterns"],
            "configurable": True,
            "config_keys": ["url"],
        },
        {
            "id": "tempo",
            "name": "Tempo",
            "type": "tempo",
            "status": "connected" if tempo_ok else "disconnected",
            "detail": tempo_detail if not tempo_ok else settings.tempo_url,
            "events": ["trace correlation", "critical path"],
            "configurable": True,
            "config_keys": ["url"],
        },
        {
            "id": "github",
            "name": "GitHub",
            "type": "github",
            "status": "connected" if github_connected else "disconnected",
            "detail": f"{settings.github_org}/{settings.github_repo}" if github_connected else "Set GITHUB_TOKEN",
            "events": ["remediation issues", "CI gate comments", "Blue PRs"],
            "configurable": True,
            "config_keys": ["token", "org", "repo", "default_branch"],
        },
        {
            "id": "pagerduty",
            "name": "PagerDuty",
            "type": "pagerduty",
            "status": "connected" if pagerduty_connected else "disconnected",
            "detail": "Incident API" if pagerduty_connected else "API key not set",
            "events": ["incident correlation", "on-call context"],
            "configurable": True,
            "config_keys": ["api_key"],
        },
        {
            "id": "slack",
            "name": "Slack",
            "type": "slack",
            "status": "connected" if slack_connected else "disconnected",
            "detail": settings.slack_approval_channel if slack_connected else "Set webhook or bot token",
            "events": ["awaiting_approval", "SLO breach", "campaign complete"],
            "configurable": True,
            "config_keys": ["webhook_url", "bot_token", "approval_channel"],
        },
        {
            "id": "anthropic",
            "name": "Anthropic (LLM)",
            "type": "anthropic",
            "status": "connected" if settings.anthropic_api_key and settings.llm_enabled else "disconnected",
            "detail": settings.anthropic_model if settings.anthropic_api_key else "API key not set",
            "events": ["composer", "remediator", "red/blue agents"],
            "configurable": True,
            "config_keys": ["api_key", "model"],
        },
    ]


async def test_integration(integration_id: str) -> dict:
    from chaos_agent.platform.connector_store import apply_connectors_to_settings

    apply_connectors_to_settings()
    settings = get_settings()
    started = time.perf_counter()

    if integration_id == "kubernetes":
        ok, message = await _check_kubernetes()
    elif integration_id == "aws":
        ok, message = await _check_aws()
    elif integration_id == "prometheus":
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
    elif integration_id == "anthropic":
        ok = bool(settings.anthropic_api_key and settings.llm_enabled)
        message = f"Model {settings.anthropic_model}" if ok else "ANTHROPIC_API_KEY not set or LLM disabled"
    else:
        return {"ok": False, "message": f"Unknown integration: {integration_id}", "latency_ms": 0}

    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return {"ok": ok, "message": message, "latency_ms": latency_ms, "integration_id": integration_id}
