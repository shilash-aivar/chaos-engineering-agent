"""Tests for observability correlator, catalog, and API."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from chaos_agent.api.app import create_app
from chaos_agent.config import Settings
from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)
from chaos_agent.observability.catalog import resolve_metrics_for_services, resolve_services_for_plan
from chaos_agent.observability.correlator import ObservabilityCorrelator
from chaos_agent.storage.database import init_db


def _sample_plan(**overrides) -> ExperimentPlan:
    base = ExperimentPlan(
        name="obs-test",
        hypothesis="test correlator",
        targets=[Target(service="checkout", namespace="staging")],
        faults=[Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="payments-api")],
        blast_radius=BlastRadius(namespace="staging", environment="staging", max_replicas_pct=20),
        watch_metrics=["checkout_error_rate", "checkout_p99"],
        rollback=RollbackSpec(type="delete_chaos_crd"),
        source=ExperimentSource.HUMAN,
    )
    return base.model_copy(update=overrides)


@pytest.fixture
def client() -> TestClient:
    import chaos_agent.config as cfg
    import chaos_agent.orchestrator.engine as engine_mod
    import chaos_agent.storage.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None
    engine_mod._engine = None
    cfg._settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        simulate_execution=True,
        experiment_max_duration_seconds=3,
        guard_interval_seconds=1,
        auto_remediate_on_complete=False,
    )
    asyncio.run(init_db())

    with TestClient(create_app()) as test_client:
        yield test_client


def test_resolve_services_from_plan() -> None:
    plan = _sample_plan()
    services = resolve_services_for_plan(
        [t.service for t in plan.targets],
        [f.target for f in plan.faults if f.target],
        plan.watch_metrics,
    )
    assert "checkout" in services
    assert "payments-api" in services


def test_resolve_metrics_includes_catalog() -> None:
    metrics = resolve_metrics_for_services(["checkout"], ["checkout_error_rate"])
    assert "checkout_error_rate" in metrics
    assert "inventory_upstream_errors" in metrics


def test_correlator_simulated_evidence() -> None:
    correlator = ObservabilityCorrelator()
    now = datetime.now(timezone.utc)
    plan = _sample_plan()
    evidence = asyncio.run(
        correlator.build_evidence(
            "exp-test",
            plan,
            baseline={"checkout_error_rate": 0.01, "checkout_p99": 0.2},
            window_start=now - timedelta(minutes=2),
            window_end=now,
            slo_breached=True,
            force_simulate=True,
        ),
    )
    assert evidence.simulated is True
    assert len(evidence.metrics) >= 2
    assert len(evidence.logs) >= 1
    assert len(evidence.traces) >= 1
    assert evidence.correlations


def test_observability_status_endpoint(client: TestClient) -> None:
    resp = client.get("/observability/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "prometheus" in body
    assert "loki" in body
    assert "tempo" in body


def test_observability_catalog_endpoint(client: TestClient) -> None:
    resp = client.get("/observability/catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert "checkout" in body["services"]


def test_experiment_captures_evidence(client: TestClient) -> None:
    from chaos_agent.orchestrator.engine import ExperimentEngine

    plan = _sample_plan()
    with (
        patch(
            "chaos_agent.orchestrator.engine.SteadyStateGuard.capture_baseline",
            new_callable=AsyncMock,
            return_value={"checkout_error_rate": 0.01, "checkout_p99": 0.2},
        ),
        patch(
            "chaos_agent.orchestrator.engine.SteadyStateGuard.wait_for_recovery",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "chaos_agent.orchestrator.engine.PrometheusClient.snapshot",
            new_callable=AsyncMock,
            return_value={"checkout_error_rate": 0.01, "checkout_p99": 0.2},
        ),
    ):
        create = client.post("/experiments", json=plan.model_dump(mode="json"))
        assert create.status_code == 200
        exp_id = create.json()["id"]
        asyncio.run(ExperimentEngine()._run(exp_id))

    detail = client.get(f"/experiments/{exp_id}")
    assert detail.json()["state"] == "complete"
    assert detail.json()["evidence"] is not None
    assert len(detail.json()["evidence"]["metrics"]) >= 1

    evidence_resp = client.get(f"/observability/evidence/{exp_id}")
    assert evidence_resp.status_code == 200
    assert evidence_resp.json()["experiment_id"] == exp_id


def test_capture_evidence_backfill(client: TestClient) -> None:
    from chaos_agent.orchestrator.engine import ExperimentEngine

    plan = _sample_plan()
    with (
        patch(
            "chaos_agent.orchestrator.engine.SteadyStateGuard.capture_baseline",
            new_callable=AsyncMock,
            return_value={"checkout_error_rate": 0.01, "checkout_p99": 0.2},
        ),
        patch(
            "chaos_agent.orchestrator.engine.SteadyStateGuard.wait_for_recovery",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "chaos_agent.orchestrator.engine.PrometheusClient.snapshot",
            new_callable=AsyncMock,
            return_value={"checkout_error_rate": 0.01, "checkout_p99": 0.2},
        ),
    ):
        create = client.post("/experiments", json=plan.model_dump(mode="json"))
        exp_id = create.json()["id"]
        asyncio.run(ExperimentEngine()._run(exp_id))

    capture = client.post(f"/observability/evidence/{exp_id}/capture")
    assert capture.status_code == 200
    assert capture.json()["experiment_id"] == exp_id
    assert len(capture.json()["metrics"]) >= 1
