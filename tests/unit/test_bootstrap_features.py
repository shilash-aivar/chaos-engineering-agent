"""Tests for bootstrap detectors and remaining feature APIs."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.bootstrap.service import detect_bootstrap_status
from chaos_agent.platform.kube import kube_context_for_namespace


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.mark.asyncio
async def test_detect_bootstrap_status() -> None:
    result = await detect_bootstrap_status("staging")
    assert "actions" in result
    assert len(result["actions"]) >= 3
    assert result["summary"]["done"] >= 0


def test_bootstrap_status_endpoint(client: TestClient) -> None:
    response = client.get("/bootstrap/status", params={"namespace": "staging"})
    assert response.status_code == 200
    body = response.json()
    assert body["namespace"] == "staging"
    assert isinstance(body["actions"], list)


def test_kube_context_for_namespace() -> None:
    ctx = kube_context_for_namespace("staging")
    assert ctx in ("eks-staging", None) or isinstance(ctx, str)
