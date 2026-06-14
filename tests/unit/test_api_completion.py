"""API route tests for completed middleware and endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.config import get_settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_integrations_test_endpoint(client: TestClient) -> None:
    response = client.post("/integrations/prometheus/test")
    assert response.status_code == 200
    body = response.json()
    assert "ok" in body
    assert "latency_ms" in body


def test_integrations_unknown(client: TestClient) -> None:
    response = client.post("/integrations/unknown/test")
    assert response.status_code == 404


def test_policies_yaml_roundtrip(client: TestClient, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from chaos_agent.platform import policies_service

    policy_file = tmp_path / "resilience-policy.yaml"
    monkeypatch.setattr(policies_service, "_ACTIVE_POLICY_PATH", policy_file)
    sample = "rules:\n  - id: test-rule\n    scope: k8s\n    require: {}\n"
    response = client.put("/policies/yaml", json={"yaml": sample})
    assert response.status_code == 200
    assert response.json()["saved"] is True
    loaded = client.get("/policies/yaml")
    assert sample.strip() in loaded.json()["yaml"]


def test_load_test_run_creates_experiment(client: TestClient) -> None:
    response = client.post("/load-tests/scenarios/checkout-peak-load/run", json={"start": False})
    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == "checkout-peak-load"
    assert body["experiment_id"]
    assert body["started"] is False


def test_plugins_ebpf_status(client: TestClient) -> None:
    response = client.get("/plugins/ebpf/status")
    assert response.status_code == 200
    body = response.json()
    assert "active_count" in body
    assert "active_programs" in body


def test_api_key_blocks_mutating_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "api_key", "secret-key")
    with TestClient(create_app()) as authed_client:
        blocked = authed_client.post("/experiments/compose", json={"scenario": "pod kill", "namespace": "staging"})
        assert blocked.status_code == 401
        allowed = authed_client.get("/health")
        assert allowed.status_code == 200
        ok = authed_client.post(
            "/experiments/compose",
            json={"scenario": "pod kill", "namespace": "staging"},
            headers={"X-API-Key": "secret-key"},
        )
        assert ok.status_code == 200
