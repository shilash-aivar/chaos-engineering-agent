"""Tests for prompt-connection chain: context, feedback, LLM gating."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.composer.feedback import load_latest_feedback
from chaos_agent.config import get_settings
from chaos_agent.llm.client import get_llm_client
from chaos_agent.platform.target_context_service import list_target_contexts


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_context_targets_endpoint(client: TestClient) -> None:
    response = client.get("/context/targets")
    assert response.status_code == 200
    contexts = response.json()["contexts"]
    assert len(contexts) >= 1
    assert "namespace" in contexts[0]


def test_list_target_contexts_from_yaml() -> None:
    contexts = list_target_contexts()
    ids = {c["id"] for c in contexts}
    assert "eks-staging" in ids


def test_llm_unavailable_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    client = get_llm_client()
    client.api_key = ""
    assert client.available is False


def test_experiments_list_namespace_filter(client: TestClient) -> None:
    response = client.get("/experiments", params={"namespace": "staging"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_load_latest_feedback_empty_namespace() -> None:
    result = await load_latest_feedback("empty-ns-no-experiments-xyz")
    assert result is None


def test_agents_status_llm_connection(client: TestClient) -> None:
    response = client.get("/agents/status")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_connection"] in ("connected", "disabled", "missing_api_key")
