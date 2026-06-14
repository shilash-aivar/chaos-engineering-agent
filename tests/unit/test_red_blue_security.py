"""Tests for Red/Blue security campaigns."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.blue.agent import defend_attack
from chaos_agent.config import Settings
from chaos_agent.red.agent import plan_attack
from chaos_agent.security.catalog import list_security_attacks
from chaos_agent.security.types import AttackCategory
from chaos_agent.storage.database import init_db


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


def test_security_attack_catalog() -> None:
    attacks = list_security_attacks()
    assert len(attacks) >= 5
    assert any(a.category == AttackCategory.HYBRID for a in attacks)
    assert all(a.safe_for_staging for a in attacks)


def test_red_plans_security_attack_when_enabled() -> None:
    gaps = [{"rule": "app-circuit-breaker", "service": "checkout", "scope": "app"}]
    attack = plan_attack(
        round_num=2,
        include_security=True,
        security_mix_pct=80,
        posture_gaps=gaps,
        prior_techniques=[],
    )
    assert attack.category in (AttackCategory.SECURITY, AttackCategory.HYBRID)


def test_blue_defends_jwt_attack() -> None:
    from chaos_agent.security.types import RedAttack

    attack = RedAttack(
        id="atk-test",
        category=AttackCategory.SECURITY,
        title="Expired JWT",
        service="payments-api",
        technique="jwt_expired_token_probe",
        description="test",
        transcript="test",
    )
    defense = defend_attack(attack)
    assert defense.artifact_type == "code"
    assert "exp" in defense.suggested_diff.lower() or "jwt" in defense.title.lower()


def test_red_blue_security_campaign_round(client: TestClient) -> None:
    start = client.post(
        "/red-blue/campaigns",
        json={
            "name": "security-game-day",
            "namespace": "staging",
            "include_security": True,
            "security_mix_pct": 70,
        },
    )
    assert start.status_code == 200
    camp = start.json()
    assert camp["include_security"] is True

    catalog = client.get("/red-blue/security/attacks")
    assert catalog.status_code == 200
    assert len(catalog.json()) >= 5

    rnd = client.post(f"/red-blue/campaigns/{camp['id']}/round")
    assert rnd.status_code == 200
    body = rnd.json()
    assert body["round"]["attack"]["title"]
    assert body["round"]["defense"]["title"]
    assert body["campaign"]["round"] == 1

    detail = client.get(f"/red-blue/campaigns/{camp['id']}")
    assert detail.status_code == 200
    assert len(detail.json()["rounds"]) == 1
