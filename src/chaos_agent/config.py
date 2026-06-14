"""Application configuration."""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CHAOS_AGENT_", extra="ignore")

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./chaos_agent.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    use_celery: bool = False
    celery_long_duration_minutes: int = 10

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    llm_enabled: bool = True
    auto_remediate_on_complete: bool = True
    inject_red_blue_faults: bool = True
    enforce_freeze_calendar: bool = False
    require_approval_production: bool = True
    aws_fis_enabled: bool = False
    auto_verify_remediation: bool = False
    slack_bot_token: str = ""
    slack_webhook_url: str = ""
    slack_approval_channel: str = "#chaos-agent-approvals"
    api_public_url: str = "http://127.0.0.1:8000"
    default_namespace: str = "staging"
    allow_prod: bool = False
    max_replica_percent: int = 30

    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3000"
    loki_url: str = "http://localhost:3100"
    tempo_url: str = "http://localhost:3200"
    toxiproxy_url: str = "http://localhost:8474"
    pagerduty_api_key: str = ""
    github_token: str = ""
    github_org: str = ""
    github_repo: str = ""
    github_default_branch: str = "main"
    staging_base_url: str = "http://localhost:8080"
    simulate_execution: bool = False
    ebpf_enabled: bool = True
    ebpf_use_tc: bool = False
    wasm_plugins_enabled: bool = True
    wasm_plugins_dir: str = "plugins/wasm"
    api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    demo_mode: bool = False
    seed_data: bool = False
    rate_limit_per_minute: int = 120
    k8s_load_test_image: str = "grafana/k6:latest"

    baseline_capture_seconds: int = 60
    guard_interval_seconds: int = 15
    steady_state_error_multiplier: float = 2.0
    steady_state_latency_multiplier: float = 3.0
    experiment_max_duration_seconds: int = 180
    rollback_ttl_seconds: int = 300


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
