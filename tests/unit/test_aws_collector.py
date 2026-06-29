"""Tests for live AWS collector wiring."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from chaos_agent.collectors.aws.collector import AwsCollector


@pytest.mark.asyncio
async def test_aws_collector_live_empty_lists_not_replaced_with_seed() -> None:
    collector = AwsCollector(region="us-east-1")

    def fake_collect() -> dict:
        return {
            "rds": [],
            "load_balancers": [],
            "sqs_queues": [],
            "elasticache": [],
            "region": "us-east-1",
            "account_id": "123456789012",
            "profile": None,
            "source": "live",
        }

    with patch.object(collector, "_collect_sync", side_effect=fake_collect):
        data = await collector.collect()

    assert data["source"] == "live"
    assert data["rds"] == []
    assert data["account_id"] == "123456789012"


def test_resolve_aws_config_uses_target_context_region() -> None:
    from chaos_agent.platform.aws import resolve_aws_config

    with patch(
        "chaos_agent.platform.aws.aws_region_for_namespace",
        return_value="eu-west-1",
    ):
        _, region = resolve_aws_config(namespace="staging")
    assert region == "eu-west-1"


@pytest.fixture
def client() -> TestClient:
    import asyncio

    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod
    from chaos_agent.api.app import create_app
    from chaos_agent.config import Settings
    from chaos_agent.storage.database import init_db

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = Settings(database_url="sqlite+aiosqlite:///:memory:", simulate_execution=True)
    asyncio.run(init_db())

    with TestClient(create_app()) as test_client:
        yield test_client


def test_aws_probe_endpoint(client: TestClient) -> None:
    mock_collector = AsyncMock()
    mock_collector.collect.return_value = {
        "source": "live",
        "region": "us-east-1",
        "account_id": "111122223333",
        "profile": "dev",
        "rds": [{"id": "app-db", "multi_az": True, "engine": "postgres"}],
        "sqs_queues": [],
        "load_balancers": [],
        "elasticache": [],
    }

    with patch("chaos_agent.collectors.aws.collector.AwsCollector", return_value=mock_collector):
        resp = client.get("/context/aws-probe", params={"namespace": "staging"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "live"
    assert body["counts"]["rds"] == 1
