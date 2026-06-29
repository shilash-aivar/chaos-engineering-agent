"""Persist and resolve connector settings from the console."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
from typing import Any, Optional

import yaml

from chaos_agent.config import Settings, get_settings

_CONNECTORS_PATH = Path(__file__).resolve().parents[3] / "config" / "connectors.yaml"
_EXAMPLE_PATH = _CONNECTORS_PATH.parent / "connectors.example.yaml"

_CACHE: dict[str, dict[str, Any]] | None = None

CONNECTOR_FIELDS: dict[str, list[dict[str, Any]]] = {
    "kubernetes": [
        {"key": "kube_context", "label": "Kube context", "type": "text", "placeholder": "eks-staging"},
        {"key": "kubeconfig_path", "label": "Kubeconfig path", "type": "text", "placeholder": "~/.kube/config"},
    ],
    "aws": [
        {"key": "profile", "label": "AWS profile", "type": "text", "placeholder": "default"},
        {"key": "region", "label": "AWS region", "type": "text", "placeholder": "us-east-1"},
    ],
    "prometheus": [
        {"key": "url", "label": "Prometheus URL", "type": "url", "placeholder": "http://localhost:9090"},
    ],
    "grafana": [
        {"key": "url", "label": "Grafana URL", "type": "url", "placeholder": "http://localhost:3000"},
    ],
    "loki": [
        {"key": "url", "label": "Loki URL", "type": "url", "placeholder": "http://localhost:3100"},
    ],
    "tempo": [
        {"key": "url", "label": "Tempo URL", "type": "url", "placeholder": "http://localhost:3200"},
    ],
    "github": [
        {"key": "token", "label": "GitHub token", "type": "password", "secret": True},
        {"key": "org", "label": "Organization", "type": "text", "placeholder": "my-org"},
        {"key": "repo", "label": "Repository", "type": "text", "placeholder": "my-repo"},
        {"key": "default_branch", "label": "Default branch", "type": "text", "placeholder": "main"},
    ],
    "pagerduty": [
        {"key": "api_key", "label": "API key", "type": "password", "secret": True},
    ],
    "slack": [
        {"key": "webhook_url", "label": "Webhook URL", "type": "password", "secret": True},
        {"key": "bot_token", "label": "Bot token", "type": "password", "secret": True},
        {"key": "approval_channel", "label": "Approval channel", "type": "text", "placeholder": "#chaos-agent-approvals"},
    ],
    "anthropic": [
        {"key": "api_key", "label": "Anthropic API key", "type": "password", "secret": True},
        {"key": "model", "label": "Model", "type": "text", "placeholder": "claude-sonnet-4-20250514"},
    ],
}


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}…{value[-4:]}"


def _load_raw() -> dict[str, dict[str, Any]]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if _CONNECTORS_PATH.exists():
        data = yaml.safe_load(_CONNECTORS_PATH.read_text()) or {}
        _CACHE = dict(data.get("connectors", {}))
        return _CACHE
    _CACHE = {}
    return _CACHE


def reload_connectors() -> None:
    global _CACHE
    _CACHE = None
    _load_raw()


def _pick(env_value: str, console_value: Any) -> str:
    if console_value is not None and str(console_value).strip():
        return str(console_value).strip()
    return env_value


def apply_connectors_to_settings(settings: Optional[Settings] = None) -> None:
    """Merge console connector file into the in-memory settings object."""
    settings = settings or get_settings()
    connectors = _load_raw()

    k8s = connectors.get("kubernetes", {})
    settings.kube_context = _pick(settings.kube_context, k8s.get("kube_context"))
    settings.kubeconfig_path = _pick(settings.kubeconfig_path, k8s.get("kubeconfig_path"))
    if settings.kubeconfig_path:
        os.environ["KUBECONFIG"] = os.path.expanduser(settings.kubeconfig_path)

    aws = connectors.get("aws", {})
    settings.aws_profile = _pick(settings.aws_profile, aws.get("profile"))
    settings.aws_region = _pick(settings.aws_region, aws.get("region"))
    if settings.aws_profile:
        os.environ["AWS_PROFILE"] = settings.aws_profile
    if settings.aws_region:
        os.environ["AWS_REGION"] = settings.aws_region

    prom = connectors.get("prometheus", {})
    settings.prometheus_url = _pick(settings.prometheus_url, prom.get("url"))

    grafana = connectors.get("grafana", {})
    settings.grafana_url = _pick(settings.grafana_url, grafana.get("url"))

    loki = connectors.get("loki", {})
    settings.loki_url = _pick(settings.loki_url, loki.get("url"))

    tempo = connectors.get("tempo", {})
    settings.tempo_url = _pick(settings.tempo_url, tempo.get("url"))

    gh = connectors.get("github", {})
    settings.github_token = _pick(settings.github_token, gh.get("token"))
    settings.github_org = _pick(settings.github_org, gh.get("org"))
    settings.github_repo = _pick(settings.github_repo, gh.get("repo"))
    settings.github_default_branch = _pick(settings.github_default_branch, gh.get("default_branch"))

    pd = connectors.get("pagerduty", {})
    settings.pagerduty_api_key = _pick(settings.pagerduty_api_key, pd.get("api_key"))

    slack = connectors.get("slack", {})
    settings.slack_webhook_url = _pick(settings.slack_webhook_url, slack.get("webhook_url"))
    settings.slack_bot_token = _pick(settings.slack_bot_token, slack.get("bot_token"))
    settings.slack_approval_channel = _pick(settings.slack_approval_channel, slack.get("approval_channel"))

    llm = connectors.get("anthropic", {})
    settings.anthropic_api_key = _pick(settings.anthropic_api_key, llm.get("api_key"))
    settings.anthropic_model = _pick(settings.anthropic_model, llm.get("model"))


def get_connector_config(integration_id: str) -> dict[str, Any]:
    if integration_id not in CONNECTOR_FIELDS:
        raise ValueError(f"Unknown connector: {integration_id}")

    apply_connectors_to_settings()
    settings = get_settings()
    stored = deepcopy(_load_raw().get(integration_id, {}))
    fields = CONNECTOR_FIELDS[integration_id]

    effective: dict[str, str] = {}
    if integration_id == "kubernetes":
        effective = {"kube_context": settings.kube_context, "kubeconfig_path": settings.kubeconfig_path}
    elif integration_id == "aws":
        effective = {"profile": settings.aws_profile, "region": settings.aws_region}
    elif integration_id == "prometheus":
        effective = {"url": settings.prometheus_url}
    elif integration_id == "grafana":
        effective = {"url": settings.grafana_url}
    elif integration_id == "loki":
        effective = {"url": settings.loki_url}
    elif integration_id == "tempo":
        effective = {"url": settings.tempo_url}
    elif integration_id == "github":
        effective = {
            "token": settings.github_token,
            "org": settings.github_org,
            "repo": settings.github_repo,
            "default_branch": settings.github_default_branch,
        }
    elif integration_id == "pagerduty":
        effective = {"api_key": settings.pagerduty_api_key}
    elif integration_id == "slack":
        effective = {
            "webhook_url": settings.slack_webhook_url,
            "bot_token": settings.slack_bot_token,
            "approval_channel": settings.slack_approval_channel,
        }
    elif integration_id == "anthropic":
        effective = {"api_key": settings.anthropic_api_key, "model": settings.anthropic_model}

    values: dict[str, Any] = {}
    for field in fields:
        key = field["key"]
        raw = stored.get(key, effective.get(key, ""))
        if field.get("secret") and raw:
            values[key] = _mask(str(raw))
            values[f"{key}_set"] = True
        else:
            values[key] = raw or ""
            values[f"{key}_set"] = bool(raw)

    return {
        "id": integration_id,
        "fields": fields,
        "values": values,
        "source": "console" if stored else "environment",
        "editable": True,
    }


def save_connector_config(integration_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if integration_id not in CONNECTOR_FIELDS:
        raise ValueError(f"Unknown connector: {integration_id}")

    allowed = {f["key"] for f in CONNECTOR_FIELDS[integration_id]}
    incoming = {k: v for k, v in payload.items() if k in allowed and v is not None}

    connectors = _load_raw()
    current = dict(connectors.get(integration_id, {}))

    for key, value in incoming.items():
        text = str(value).strip()
        if not text:
            current.pop(key, None)
            continue
        field = next(f for f in CONNECTOR_FIELDS[integration_id] if f["key"] == key)
        if field.get("secret") and ("…" in text or text == "••••••••"):
            continue
        current[key] = text

    connectors[integration_id] = current
    _CONNECTORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONNECTORS_PATH.write_text(yaml.safe_dump({"connectors": connectors}, sort_keys=False))

    global _CACHE
    _CACHE = connectors
    apply_connectors_to_settings()

    return {"saved": True, "id": integration_id, "path": str(_CONNECTORS_PATH)}


def ensure_example_file() -> None:
    if _EXAMPLE_PATH.exists():
        return
    example = {
        "connectors": {
            "kubernetes": {"kube_context": "eks-staging", "kubeconfig_path": "~/.kube/config"},
            "aws": {"profile": "default", "region": "us-east-1"},
            "prometheus": {"url": "http://localhost:9090"},
            "grafana": {"url": "http://localhost:3000"},
            "loki": {"url": "http://localhost:3100"},
            "tempo": {"url": "http://localhost:3200"},
            "github": {"org": "my-org", "repo": "my-repo", "default_branch": "main"},
            "slack": {"approval_channel": "#chaos-agent-approvals"},
        },
    }
    _EXAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _EXAMPLE_PATH.write_text(yaml.safe_dump(example, sort_keys=False))
