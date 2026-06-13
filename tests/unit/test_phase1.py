import pytest

from chaos_agent.composer.rules import compose_from_scenario
from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)
from chaos_agent.orchestrator.guards.steady_state import SteadyStateGuard


def _sample_plan(**overrides) -> ExperimentPlan:
    base = ExperimentPlan(
        name="test-exp",
        hypothesis="test",
        targets=[Target(service="checkout", namespace="staging")],
        faults=[Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="checkout")],
        blast_radius=BlastRadius(namespace="staging", environment="staging"),
        watch_metrics=["checkout_error_rate"],
        rollback=RollbackSpec(type="delete_chaos_crd"),
        source=ExperimentSource.HUMAN,
    )
    return base.model_copy(update=overrides)


def test_validate_plan_rejects_prod_by_default() -> None:
    plan = _sample_plan(blast_radius=BlastRadius(namespace="staging", environment="production"))
    with pytest.raises(SafetyValidationError, match="production"):
        validate_plan(plan)


def test_validate_plan_rejects_excessive_blast_radius() -> None:
    plan = _sample_plan(blast_radius=BlastRadius(namespace="staging", max_replicas_pct=50))
    with pytest.raises(SafetyValidationError, match="blast radius"):
        validate_plan(plan)


def test_steady_state_guard_detects_error_breach() -> None:
    guard = SteadyStateGuard()
    baseline = {"checkout_error_rate": 0.01}
    current = {"checkout_error_rate": 0.05}
    result = guard.check(baseline, current)
    assert result.breached is True
    assert result.metric == "checkout_error_rate"


def test_steady_state_guard_no_breach_within_threshold() -> None:
    guard = SteadyStateGuard()
    baseline = {"checkout_p99": 0.2}
    current = {"checkout_p99": 0.4}
    result = guard.check(baseline, current)
    assert result.breached is False


def test_compose_pod_kill_scenario() -> None:
    import asyncio

    plan, summary = asyncio.run(compose_from_scenario("pod kill on payments-api", "staging"))
    assert plan.faults[0].type == "pod_kill"
    assert plan.faults[0].target == "payments-api"
    assert summary


def test_compose_db_blackhole_scenario() -> None:
    import asyncio

    plan, summary = asyncio.run(
        compose_from_scenario("payments DB loses connectivity during checkout", "staging"),
    )
    executors = {f.executor.value for f in plan.faults}
    assert "toxiproxy" in executors


def test_compose_latency_scenario() -> None:
    import asyncio

    plan, _ = asyncio.run(compose_from_scenario("inventory API slow latency test", "staging"))
    types = {f.type for f in plan.faults}
    assert "network_latency" in types
