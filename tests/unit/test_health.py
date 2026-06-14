import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert "components" in body
    assert "database" in body["components"]
    assert response.headers.get("X-Request-ID")


def test_request_id_header(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "test-req-1"})
    assert response.headers.get("X-Request-ID") == "test-req-1"
