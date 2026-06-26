"""Unit tests for LLM agent layer (mocked — no API key required)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from chaos_agent.composer.service import compose_full, compose_scenario
from chaos_agent.llm.client import LLMClient, _parse_json_object
from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)
from chaos_agent.observability.types import FaultWindowEvidence, MetricWindowSample
from chaos_agent.referee.scorer import score_round
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution
from chaos_agent.remediator.analyzer import analyze_evidence_rules
from chaos_agent.remediator.pipeline import run_remediation_pipeline
from chaos_agent.security.types import AttackCategory, BlueDefense, RedAttack


def test_parse_json_object_from_fence() -> None:
    text = 'Here is the plan:\n```json\n{"name": "test", "faults": []}\n```'
    data = _parse_json_object(text)
    assert data is not None
    assert data["name"] == "test"


def test_llm_client_unavailable_without_key() -> None:
    client = LLMClient()
    with patch.object(client, "api_key", ""):
        assert client.available is False


@pytest.mark.asyncio
async def test_compose_scenario_falls_back_to_rules() -> None:
    with patch("chaos_agent.composer.llm.get_llm_client") as mock_llm:
        mock_llm.return_value.available = False
        plan, summary, mode = await compose_scenario("pod kill on checkout", "staging")
    assert mode == "rules"
    assert plan.faults[0].type == "pod_kill"
    assert summary


@pytest.mark.asyncio
async def test_compose_scenario_uses_llm_when_available() -> None:
    llm_plan = {
        "name": "llm-checkout-kill",
        "hypothesis": "kill checkout pod",
        "targets": [{"service": "checkout", "namespace": "staging"}],
        "faults": [{"executor": "chaos_mesh", "type": "pod_kill", "target": "checkout"}],
        "blast_radius": {"namespace": "staging", "environment": "staging", "max_replicas_pct": 30},
        "watch_metrics": ["checkout_error_rate"],
        "rollback": {"type": "delete_chaos_crd", "ttl_seconds": 300},
        "summary": "LLM mapped pod kill",
    }
    with patch("chaos_agent.composer.llm.get_llm_client") as mock_llm:
        mock_llm.return_value.available = True
        mock_llm.return_value.complete_json = AsyncMock(return_value=llm_plan)
        plan, summary, mode = await compose_scenario("kill checkout", "staging")
    assert mode == "llm"
    assert plan.source == ExperimentSource.LLM
    assert plan.name == "llm-checkout-kill"


def test_analyze_evidence_rules_detects_slo_breach() -> None:
    plan = ExperimentPlan(
        name="test",
        hypothesis="test",
        targets=[Target(service="checkout", namespace="staging")],
        faults=[Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="checkout")],
        blast_radius=BlastRadius(namespace="staging"),
        watch_metrics=["checkout_error_rate"],
        rollback=RollbackSpec(type="delete_chaos_crd"),
        infra_evidence=["checkout: no retry configured"],
    )
    evidence = FaultWindowEvidence(
        experiment_id="exp-test",
        window_start=datetime.now(timezone.utc),
        window_end=datetime.now(timezone.utc),
        metrics=[
            MetricWindowSample(name="checkout_error_rate", baseline=0.01, during_peak=0.05, delta_ratio=5.0),
        ],
    )
    findings = analyze_evidence_rules(
        experiment_id="exp-test",
        plan=plan,
        evidence=evidence,
        slo_breached=True,
    )
    assert len(findings) >= 2
    assert any(f.severity.value == "critical" for f in findings)


def test_referee_rejects_high_blast_pod_kill() -> None:
    plan = ExperimentPlan(
        name="test",
        hypothesis="test",
        targets=[Target(service="checkout", namespace="staging")],
        faults=[Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="checkout")],
        blast_radius=BlastRadius(namespace="staging", max_replicas_pct=25),
        watch_metrics=["checkout_error_rate"],
        rollback=RollbackSpec(type="delete_chaos_crd"),
    )
    with pytest.raises(RefereeValidationError, match="blast radius"):
        validate_plan_for_execution(plan)


@pytest.mark.asyncio
async def test_remediation_pipeline_skips_without_evidence() -> None:
    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod
    from chaos_agent.config import Settings
    from chaos_agent.storage.database import init_db

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = Settings(database_url="sqlite+aiosqlite:///:memory:")
    await init_db()

    result = await run_remediation_pipeline("exp-does-not-exist")
    assert result.mode == "skipped"


@pytest.mark.asyncio
async def test_compose_full_includes_premortem_and_referee() -> None:
    with patch("chaos_agent.composer.llm.get_llm_client") as mock_llm:
        mock_llm.return_value.available = False
        result = await compose_full("pod kill on checkout", "staging")
    assert result["composer"] == "rules"
    assert "pre_mortem" in result
    assert result["referee"]["passed"] is True


def test_score_round_uses_inject_result() -> None:
    attack = RedAttack(
        id="a1",
        category=AttackCategory.RESILIENCE,
        title="Pod kill",
        service="checkout",
        technique="pod_kill",
        description="kill pod",
        transcript="Red strikes",
    )
    defense = BlueDefense(
        attack_id="a1",
        category=AttackCategory.RESILIENCE,
        title="Priority class",
        action="patch",
        artifact_type="manifest",
        target_path="k8s/checkout.yaml",
        suggested_diff="+ priorityClassName: critical",
        transcript="Blue responds",
    )
    result = score_round(
        round_num=1,
        attack=attack,
        defense=defense,
        posture_gaps=[],
        inject_result={"experiment_id": "exp-x", "state": "complete", "slo_breached": False, "injected": True},
    )
    assert any("exp-x" in line for line in result.red_transcript)


@pytest.mark.asyncio
async def test_export_equilibrium_persists_suite() -> None:
    from chaos_agent.referee.service import export_equilibrium_round
    from chaos_agent.security.types import AttackCategory, BlueDefense, RedAttack, RoundResult
    from chaos_agent.storage.database import init_db, get_session_factory
    from chaos_agent.storage.repositories.campaign import CampaignRepository
    import chaos_agent.config as cfg
    import chaos_agent.storage.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None
    cfg._settings = None
    await init_db()

    attack = RedAttack(
        id="a1",
        category=AttackCategory.RESILIENCE,
        title="Latency",
        service="checkout",
        technique="network_latency",
        description="slow",
        transcript="red",
    )
    defense = BlueDefense(
        attack_id="a1",
        category=AttackCategory.RESILIENCE,
        title="Retry",
        action="patch",
        artifact_type="code",
        target_path="app.py",
        suggested_diff="+ retry",
        transcript="blue",
    )
    round_result = RoundResult(
        round=1,
        attack=attack,
        defense=defense,
        red_points=50,
        blue_points=50,
        outcome="draw",
        referee_note="equilibrium",
        red_transcript=["r"],
        blue_transcript=["b"],
    )

    import uuid

    camp_id = f"camp-export-{uuid.uuid4().hex[:8]}"
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        await repo.seed_if_empty()
        camp = {
            "id": camp_id,
            "name": "Export test",
            "namespace": "staging",
            "state": "complete",
            "round": 1,
            "max_rounds": 1,
            "red_score": 50,
            "blue_score": 50,
            "leader": "draw",
            "include_security": False,
            "security_mix_pct": 0,
            "attack_framework_id": None,
            "attack_plan_id": None,
            "planned_attack_count": 0,
            "last_round_at": "2026-01-01T00:00:00+00:00",
            "rounds": [round_result.model_dump(mode="json")],
        }
        await repo.save_campaign(camp)

    result = await export_equilibrium_round(camp_id, 1)
    assert result["exported"] is True
    assert result["suite"]["source"] == "red_blue"


def test_slack_client_dry_run_without_token() -> None:
    from chaos_agent.integrations.slack.client import SlackClient

    client = SlackClient()
    assert client.available is False


def test_production_skip_gate_for_pending_approval() -> None:
    plan = ExperimentPlan(
        name="prod-test",
        hypothesis="test",
        targets=[Target(service="checkout", namespace="production")],
        faults=[Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="checkout")],
        blast_radius=BlastRadius(namespace="production", environment="production", max_replicas_pct=10),
        watch_metrics=["checkout_error_rate"],
        rollback=RollbackSpec(type="delete_chaos_crd"),
    )
    with patch("chaos_agent.composer.validators.safety.get_settings") as mock_settings:
        mock_settings.return_value.allow_prod = True
        mock_settings.return_value.max_replica_percent = 30
        validate_plan_for_execution(plan, skip_production_gate=True)
        with pytest.raises(RefereeValidationError, match="referee approval"):
            validate_plan_for_execution(plan)
