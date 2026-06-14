"""Runtime and posture policy exposure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from chaos_agent.config import get_settings

_POLICY_PATH = Path(__file__).resolve().parents[3] / "config" / "policies" / "resilience-policy.example.yaml"


def get_runtime_policies() -> list[dict[str, Any]]:
    settings = get_settings()
    return [
        {
            "id": "max-replica-percent",
            "name": "Max replica blast radius",
            "value": f"{settings.max_replica_percent}%",
            "enforced": True,
            "description": "Hard cap on pods affected per fault",
        },
        {
            "id": "allow-prod",
            "name": "Production experiments",
            "value": "allowed" if settings.allow_prod else "blocked",
            "enforced": True,
            "description": "Requires CHAOS_AGENT_ALLOW_PROD=true",
        },
        {
            "id": "steady-state-error",
            "name": "Error rate multiplier",
            "value": f"{settings.steady_state_error_multiplier}×",
            "enforced": True,
            "description": "Abort when error rate exceeds baseline × multiplier",
        },
        {
            "id": "steady-state-latency",
            "name": "Latency multiplier",
            "value": f"{settings.steady_state_latency_multiplier}×",
            "enforced": True,
            "description": "Abort when p99 exceeds baseline × multiplier",
        },
        {
            "id": "experiment-max-duration",
            "name": "Max experiment duration",
            "value": f"{settings.experiment_max_duration_seconds}s",
            "enforced": True,
            "description": "Auto-rollback after duration",
        },
        {
            "id": "rollback-ttl",
            "name": "Rollback TTL safety net",
            "value": f"{settings.rollback_ttl_seconds}s",
            "enforced": True,
            "description": "Second rollback attempt after TTL",
        },
        {
            "id": "llm-enabled",
            "name": "LLM agents",
            "value": "on" if settings.llm_enabled else "off",
            "enforced": settings.llm_enabled,
            "description": "Composer, Remediator, Red, Blue use Anthropic when key set",
        },
    ]


def get_executor_allowlist() -> list[dict[str, str]]:
    settings = get_settings()
    fis_status = "enabled" if settings.aws_fis_enabled else "disabled"
    fis_detail = "AZ impairment, RDS failover" if settings.aws_fis_enabled else "Set CHAOS_AGENT_AWS_FIS_ENABLED=true"
    return [
        {"name": "chaos_mesh", "status": "enabled", "detail": "pod_kill, network_latency, io_stress"},
        {"name": "toxiproxy", "status": "enabled", "detail": "dependency_blackhole, timeout, latency"},
        {"name": "k6", "status": "enabled", "detail": "load scenarios paired with faults"},
        {"name": "aws_fis", "status": fis_status, "detail": fis_detail},
    ]


def get_posture_rules() -> list[dict[str, Any]]:
    if not _POLICY_PATH.exists():
        return []
    data = yaml.safe_load(_POLICY_PATH.read_text()) or {}
    rules = []
    for rule in data.get("rules", []):
        rules.append(
            {
                "id": rule.get("id"),
                "scope": rule.get("scope"),
                "severity": rule.get("severity", "medium"),
                "summary": f"require {rule.get('require', {})}",
            },
        )
    return rules


def get_policy_yaml() -> str:
    if _POLICY_PATH.exists():
        return _POLICY_PATH.read_text()
    return "# resilience-policy.yaml not found\n"
