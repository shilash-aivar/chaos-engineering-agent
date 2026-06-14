"""Tests for SAST, CI gate, campaign persistence."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.config import Settings
from chaos_agent.security.scanners.sast import run_sast_scan
from chaos_agent.storage.database import init_db


@pytest.fixture
def client() -> TestClient:
    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = Settings(database_url="sqlite+aiosqlite:///:memory:", simulate_execution=True)
    asyncio.run(init_db())

    with TestClient(create_app()) as test_client:
        yield test_client


def test_sast_finds_tf_and_code_issues() -> None:
    result = run_sast_scan(
        terraform_files={"infra/rds.tf": 'multi_az = false\npassword = "secret"'},
        code_files={"src/a.py": "client = httpx.AsyncClient()\npassword = 'x'"},
    )
    assert len(result.findings) >= 2
    assert result.simulated is True


def test_ci_gate_evaluate(client: TestClient) -> None:
    resp = client.post(
        "/ci-gate/evaluate",
        json={
            "pr_number": 99,
            "changed_files": ["src/api/routes.py", "infra/main.tf"],
            "changed_services": ["payments-api"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["probes"]) <= 3
    assert body["fault"]["type"]
    assert "OWASP" in body["comment_markdown"]


def test_campaign_persists_attack_plan(client: TestClient) -> None:
    gen = client.post(
        "/red-blue/security/generate",
        json={"framework_id": "owasp-top10-2021", "category_ids": ["A07"]},
    )
    plan_id = gen.json()["plan_id"]

    start = client.post(
        "/red-blue/campaigns",
        json={"name": "persist-test", "attack_plan_id": plan_id, "include_security": True},
    )
    camp_id = start.json()["id"]

    rnd = client.post(f"/red-blue/campaigns/{camp_id}/round")
    assert rnd.status_code == 200

    rem = client.post(f"/red-blue/campaigns/{camp_id}/rounds/1/remediate")
    assert rem.status_code == 200
    assert rem.json()["dry_run"] is True

    verify = client.post(f"/red-blue/campaigns/{camp_id}/rounds/1/verify")
    assert verify.status_code == 200
    assert "verified" in verify.json()


def test_context_ingest_includes_sast(client: TestClient) -> None:
    resp = client.post(
        "/context/ingest",
        json={
            "repo_name": "payments",
            "terraform_files": {"infra/rds.tf": "multi_az = false"},
            "code_files": {"src/x.py": "password = 'hardcoded'"},
        },
    )
    assert resp.status_code == 200
    analysis = resp.json()["analysis"]
    assert len(analysis.get("sast_findings", [])) >= 1
