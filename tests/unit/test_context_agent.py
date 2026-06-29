"""Tests for context understanding agent."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.config import Settings
from chaos_agent.context.agent.loop import run_context_agent
from chaos_agent.storage.database import init_db


@pytest.fixture
def client() -> TestClient:
    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        simulate_execution=True,
        llm_enabled=False,
    )
    asyncio.run(init_db())

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_context_agent_rules_fallback() -> None:
    result = await run_context_agent(
        problem_statement="Test payments resilience under DB failure",
        namespace="staging",
    )
    assert result["mode"] == "rules"
    assert result["summary"]
    assert result["infrastructure_overview"]
    assert len(result["tool_trace"]) >= 5
    assert result["confidence"] in ("high", "medium", "low")


def test_context_agent_api(client: TestClient) -> None:
    response = client.post(
        "/agents/context/understand",
        json={
            "problem_statement": "Understand checkout path resilience",
            "namespace": "staging",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] in ("llm", "rules")
    assert body["summary"]
    assert "tool_trace" in body
