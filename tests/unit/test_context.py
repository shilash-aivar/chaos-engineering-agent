"""Tests for context ingestion pipeline."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.blue.agent import suggest_fixes
from chaos_agent.config import Settings
from chaos_agent.context.analyzer import analyze_context
from chaos_agent.context.ingest import ingest_context
from chaos_agent.context.parsers.terraform import parse_terraform
from chaos_agent.context.types import ContextGap, PracticeLevel
from chaos_agent.storage.database import init_db


SAMPLE_TF = """
resource "aws_db_instance" "payments_db" {
  identifier = "payments-db"
  multi_az   = false
}

resource "aws_sqs_queue" "order_events" {
  name = "order-events"
}
"""

SAMPLE_README = """
# payments-service
Highly available payment processing.
SLO: 99.9% availability with error budget tracking.
"""


@pytest.fixture
def client() -> TestClient:
    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        simulate_execution=True,
    )
    asyncio.run(init_db())

    with TestClient(create_app()) as test_client:
        yield test_client


def test_terraform_parser_extracts_resources() -> None:
    resources = parse_terraform(SAMPLE_TF, source_file="infra/rds.tf")
    types = {r.type for r in resources}
    assert "aws_db_instance" in types
    assert "aws_sqs_queue" in types

    rds = next(r for r in resources if r.type == "aws_db_instance")
    assert rds.name == "payments_db"
    assert rds.attributes.get("multi_az") is False
    assert rds.source_file == "infra/rds.tf"


@pytest.mark.asyncio
async def test_analyze_context_produces_gaps() -> None:
    snapshot = ingest_context(
        repo_name="payments-service",
        namespace="staging",
        terraform_files={"infra/rds.tf": SAMPLE_TF},
        readme_content=SAMPLE_README,
        code_files={"src/client.py": "client = httpx.AsyncClient()"},
    )
    gaps, summary = await analyze_context(snapshot, "staging")

    assert len(gaps) >= 1
    assert "k8s" in summary or "aws" in summary
    rules = {g.rule for g in gaps}
    assert "critical-rds-multi-az" in rules or "declared-ha-mismatch" in rules


@pytest.mark.asyncio
async def test_blue_suggestions_for_rds_gap() -> None:
    gap = ContextGap(
        id="ctx-001",
        level=PracticeLevel.DB,
        scope="aws",
        severity="critical",
        service="payments-db",
        rule="critical-rds-multi-az",
        message="RDS instance is not Multi-AZ",
        observed_evidence=["payments-db multi_az=false"],
    )
    suggestions = suggest_fixes([gap])
    assert len(suggestions) == 1
    assert suggestions[0].artifact_type == "terraform"
    assert "multi_az" in suggestions[0].suggested_diff


def test_context_ingest_api(client: TestClient) -> None:
    response = client.post(
        "/context/ingest",
        json={
            "repo_name": "payments-service",
            "namespace": "staging",
            "terraform_files": {"infra/rds.tf": SAMPLE_TF},
            "readme_content": SAMPLE_README,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["repo_name"] == "payments-service"
    assert len(body["analysis"]["gaps"]) >= 1
    assert len(body["analysis"]["blue_suggestions"]) >= 1

    snapshot_resp = client.get("/context/snapshot", params={"namespace": "staging"})
    assert snapshot_resp.status_code == 200

    analysis_resp = client.get("/context/analysis", params={"namespace": "staging"})
    assert analysis_resp.status_code == 200
    assert analysis_resp.json()["snapshot_id"] == body["snapshot"]["id"]
