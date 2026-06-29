"""Tests for context ingestion pipeline."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.blue.agent import suggest_fixes
from chaos_agent.config import Settings
from chaos_agent.context.analyzer import analyze_context
from chaos_agent.context.ingest import ingest_context
from chaos_agent.context.parsers.manifests import parse_manifest
from chaos_agent.context.parsers.terraform import parse_terraform
from chaos_agent.context.sources.files import classify_files
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


def test_terraform_parser_keeps_nested_hcl_blocks() -> None:
    resources = parse_terraform(
        '''
resource "aws_sqs_queue" "orders" {
  name = "orders"
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 5
  })
}
''',
        source_file="infra/sqs.tf",
    )
    queue = next(r for r in resources if r.type == "aws_sqs_queue")
    assert queue.attributes["name"] == "orders"
    assert "redrive_policy" in queue.attributes


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
    assert "understanding" in analysis_resp.json()


def test_classify_files_buckets_by_type() -> None:
    classified = classify_files(
        {
            "infra/main.tf": 'resource "aws_sqs_queue" "q" { name = "x" }',
            "README.md": "# service\nMulti-AZ database",
            "k8s/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nreadinessProbe:",
            "src/app.py": "client = httpx.AsyncClient()",
        },
    )
    assert "infra/main.tf" in classified.terraform_files
    assert classified.readme_content is not None
    assert "k8s/deployment.yaml" in classified.manifest_files
    assert "src/app.py" in classified.code_files


def test_manifest_parser_extracts_probes() -> None:
    hints = parse_manifest("apiVersion: apps/v1\nkind: Deployment\nreadinessProbe:\n  httpGet:", "deploy.yaml")
    assert any("Readiness probe" in h for h in hints)


def test_context_snapshots_list_and_delete(client: TestClient) -> None:
    client.post(
        "/context/ingest",
        json={
            "repo_name": "svc-a",
            "namespace": "staging",
            "terraform_files": {"infra/rds.tf": SAMPLE_TF},
        },
    )
    listed = client.get("/context/snapshots", params={"namespace": "staging"})
    assert listed.status_code == 200
    snapshots = listed.json()["snapshots"]
    assert len(snapshots) >= 1
    snap_id = snapshots[0]["id"]

    understanding = client.get("/context/understanding", params={"namespace": "staging", "snapshot_id": snap_id})
    assert understanding.status_code == 200
    assert "alignment" in understanding.json()["understanding"]

    deleted = client.delete(f"/context/snapshots/{snap_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_ingest_raw_files(client: TestClient) -> None:
    response = client.post(
        "/context/ingest",
        json={
            "repo_name": "raw-upload",
            "namespace": "staging",
            "raw_files": {
                "infra/rds.tf": SAMPLE_TF,
                "README.md": SAMPLE_README,
                "k8s/deploy.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: checkout",
            },
        },
    )
    assert response.status_code == 200
    summary = response.json()["analysis"]["declared_summary"]
    assert summary["terraform_resources"] >= 1
    assert summary["manifest_hints"] >= 1
