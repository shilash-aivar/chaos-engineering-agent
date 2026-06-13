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

    anthropic_api_key: str = ""
    default_namespace: str = "staging"
    allow_prod: bool = False
    max_replica_percent: int = 30

    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3000"
    tempo_url: str = "http://localhost:3200"
    toxiproxy_url: str = "http://localhost:8474"
    pagerduty_api_key: str = ""
    github_token: str = ""
    github_org: str = ""
    github_repo: str = ""
    simulate_execution: bool = False

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
