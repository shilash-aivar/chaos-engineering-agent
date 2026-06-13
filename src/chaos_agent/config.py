"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CHAOS_AGENT_", extra="ignore")

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://chaos:chaos@localhost:5432/chaos_agent"
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""
    default_namespace: str = "staging"
    allow_prod: bool = False
    max_replica_percent: int = 30


def get_settings() -> Settings:
    return Settings()
