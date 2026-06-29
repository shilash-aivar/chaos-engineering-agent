"""Connector console configuration tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.config import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from chaos_agent.platform import connector_store

    connectors_file = tmp_path / "connectors.yaml"
    monkeypatch.setattr(connector_store, "_CONNECTORS_PATH", connectors_file)
    connector_store.reload_connectors()
    return TestClient(create_app())


def test_connector_config_roundtrip(client: TestClient) -> None:
    response = client.put(
        "/integrations/prometheus/config",
        json={"values": {"url": "http://prom.example:9090"}},
    )
    assert response.status_code == 200
    assert response.json()["saved"] is True

    loaded = client.get("/integrations/prometheus/config")
    assert loaded.status_code == 200
    body = loaded.json()
    assert body["values"]["url"] == "http://prom.example:9090"

    settings = get_settings()
    assert settings.prometheus_url == "http://prom.example:9090"


def test_connector_secret_masking(client: TestClient) -> None:
    client.put(
        "/integrations/github/config",
        json={
            "values": {
                "token": "ghp_testtoken123456",
                "org": "acme",
                "repo": "platform",
            },
        },
    )
    loaded = client.get("/integrations/github/config").json()
    assert loaded["values"]["token_set"] is True
    assert "…" in loaded["values"]["token"]
    assert loaded["values"]["org"] == "acme"


def test_connector_test_after_save(client: TestClient) -> None:
    client.put("/integrations/pagerduty/config", json={"values": {"api_key": "pd-key-abc"}})
    response = client.post("/integrations/pagerduty/test")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_kubernetes_connector_listed(client: TestClient) -> None:
    response = client.get("/integrations")
    assert response.status_code == 200
    ids = {i["id"] for i in response.json()["integrations"]}
    assert "kubernetes" in ids
    assert "aws" in ids


def test_kubernetes_connector_config_roundtrip(client: TestClient) -> None:
    response = client.put(
        "/integrations/kubernetes/config",
        json={"values": {"kube_context": "eks-prod"}},
    )
    assert response.status_code == 200
    loaded = client.get("/integrations/kubernetes/config").json()
    assert loaded["values"]["kube_context"] == "eks-prod"
