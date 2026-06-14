"""Runtime and posture policy exposure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from chaos_agent.config import get_settings
from chaos_agent.plugins.wasm_host import WasmHost

_host = WasmHost()

_POLICY_PATH = Path(__file__).resolve().parents[3] / "config" / "policies" / "resilience-policy.example.yaml"
_ACTIVE_POLICY_PATH = _POLICY_PATH.parent / "resilience-policy.yaml"


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
        {
            "id": "ebpf-enabled",
            "name": "eBPF fault executor",
            "value": "on" if settings.ebpf_enabled else "off",
            "enforced": settings.ebpf_enabled,
            "description": "Kernel-level network latency, packet loss, connect block",
        },
        {
            "id": "wasm-plugins",
            "name": "Wasm policy plugins",
            "value": _host.runtime if settings.wasm_plugins_enabled else "disabled",
            "enforced": settings.wasm_plugins_enabled,
            "description": "Referee blast-radius and posture gap checks via Wasm",
        },
    ]


def get_executor_allowlist() -> list[dict[str, str]]:
    settings = get_settings()
    fis_status = "enabled" if settings.aws_fis_enabled else "disabled"
    fis_detail = "AZ impairment, RDS failover" if settings.aws_fis_enabled else "Set CHAOS_AGENT_AWS_FIS_ENABLED=true"
    ebpf_status = "enabled" if settings.ebpf_enabled else "disabled"
    ebpf_detail = (
        "network_latency, packet_loss, connect_block, syscall_delay"
        if settings.ebpf_enabled
        else "Set CHAOS_AGENT_EBPF_ENABLED=true"
    )
    return [
        {"name": "chaos_mesh", "status": "enabled", "detail": "pod_kill, network_latency, io_stress"},
        {"name": "toxiproxy", "status": "enabled", "detail": "dependency_blackhole, timeout, latency"},
        {"name": "k6", "status": "enabled", "detail": "load scenarios paired with faults"},
        {"name": "aws_fis", "status": fis_status, "detail": fis_detail},
        {"name": "ebpf", "status": ebpf_status, "detail": ebpf_detail},
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
    if _ACTIVE_POLICY_PATH.exists():
        return _ACTIVE_POLICY_PATH.read_text()
    if _POLICY_PATH.exists():
        return _POLICY_PATH.read_text()
    return "# resilience-policy.yaml not found\n"


def save_policy_yaml(content: str) -> dict[str, Any]:
    parsed = yaml.safe_load(content)
    if parsed is None:
        raise ValueError("Policy YAML is empty")
    if not isinstance(parsed, dict):
        raise ValueError("Policy YAML root must be a mapping")
    if "rules" not in parsed or not isinstance(parsed["rules"], list):
        raise ValueError("Policy YAML must include a top-level 'rules' list")
    _ACTIVE_POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVE_POLICY_PATH.write_text(content)
    return {
        "saved": True,
        "path": str(_ACTIVE_POLICY_PATH),
        "rules_count": len(parsed["rules"]),
    }
