"""Tests for attack framework catalog and generation."""

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.security.frameworks.registry import list_frameworks
from chaos_agent.security.generator import generate_attack_plan


def test_list_frameworks_includes_owasp_mitre_cwe() -> None:
    ids = {f.id for f in list_frameworks()}
    assert "owasp-top10-2021" in ids
    assert "mitre-attack-enterprise" in ids
    assert "cwe-top25-2023" in ids


def test_owasp_generates_attack_per_cwe() -> None:
    plan = generate_attack_plan(framework_id="owasp-top10-2021", namespace="staging")
    assert plan.framework_id == "owasp-top10-2021"
    assert plan.total_cwes >= 30
    assert plan.total_cve_examples >= 60
    assert len(plan.attacks) == plan.total_cwes
    ranks = {a.owasp_rank for a in plan.attacks}
    assert "A01" in ranks
    assert "A10" in ranks
    for attack in plan.attacks:
        assert attack.cwe
        assert attack.cwe_ids
        assert attack.cve_examples
        assert attack.safe_for_staging


def test_owasp_single_category_filter() -> None:
    plan = generate_attack_plan(
        framework_id="owasp-top10-2021",
        category_ids=["A07"],
    )
    assert all(a.owasp_rank == "A07" for a in plan.attacks)
    assert plan.total_cwes == 4


def test_mitre_generates_attacks() -> None:
    plan = generate_attack_plan(framework_id="mitre-attack-enterprise")
    assert len(plan.attacks) >= 10
    assert any(a.mitre_technique_id == "T1190" for a in plan.attacks)


@pytest.fixture
def client() -> TestClient:
    import asyncio

    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod
    from chaos_agent.config import Settings
    from chaos_agent.storage.database import init_db

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = Settings(database_url="sqlite+aiosqlite:///:memory:", simulate_execution=True)
    asyncio.run(init_db())

    with TestClient(create_app()) as test_client:
        yield test_client


def test_api_generate_owasp_plan(client: TestClient) -> None:
    frameworks = client.get("/red-blue/security/frameworks")
    assert frameworks.status_code == 200
    assert len(frameworks.json()) >= 4

    owasp = client.get("/red-blue/security/frameworks/owasp-top10-2021")
    assert owasp.status_code == 200
    assert len(owasp.json()["categories"]) == 10

    gen = client.post(
        "/red-blue/security/generate",
        json={"framework_id": "owasp-top10-2021", "namespace": "staging"},
    )
    assert gen.status_code == 200
    body = gen.json()
    assert body["plan_id"]
    assert len(body["attacks"]) >= 30

    camp = client.post(
        "/red-blue/campaigns",
        json={
            "name": "owasp-full-scan",
            "include_security": True,
            "attack_plan_id": body["plan_id"],
        },
    )
    assert camp.status_code == 200
    assert camp.json()["planned_attack_count"] >= 30
