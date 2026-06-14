"""Unit tests for eBPF executor and Wasm plugin host."""

from __future__ import annotations

import pytest

from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.executors.ebpf.executor import EbpfExecutor
from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)
from chaos_agent.observability.correlator import ObservabilityCorrelator
from chaos_agent.plugins.wasm_host import WasmHost
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution


def _ebpf_plan(**kwargs) -> ExperimentPlan:
    defaults = {
        "name": "ebpf-latency",
        "hypothesis": "latency degrades checkout",
        "targets": [Target(service="checkout", namespace="staging")],
        "faults": [
            Fault(
                executor=FaultExecutor.EBPF,
                type="network_latency",
                target="checkout",
                params={"latency_ms": 200},
            ),
        ],
        "blast_radius": BlastRadius(namespace="staging", max_replicas_pct=10),
        "watch_metrics": ["checkout_error_rate"],
        "rollback": RollbackSpec(type="delete_ebpf_program"),
        "source": ExperimentSource.HUMAN,
    }
    defaults.update(kwargs)
    return ExperimentPlan(**defaults)


@pytest.mark.asyncio
async def test_ebpf_executor_apply_and_rollback() -> None:
    executor = EbpfExecutor(simulate=True)
    fault = Fault(
        executor=FaultExecutor.EBPF,
        type="network_latency",
        target="checkout",
        params={"latency_ms": 150},
    )
    handle = await executor.apply("exp-ebpf-1", fault, "staging", 10.0)
    assert handle.executor == "ebpf"
    assert handle.simulated is True
    await executor.rollback(handle)


def test_ebpf_plan_passes_safety() -> None:
    validate_plan(_ebpf_plan())


def test_ebpf_disabled_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from chaos_agent.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "ebpf_enabled", False)
    with pytest.raises(SafetyValidationError, match="ebpf executor disabled"):
        validate_plan(_ebpf_plan())


def test_wasm_blast_radius_passes() -> None:
    host = WasmHost()
    result = host.validate_blast_radius(15)
    assert result.passed is True


def test_wasm_blast_radius_fails() -> None:
    host = WasmHost()
    result = host.validate_blast_radius(25)
    assert result.passed is False


def test_referee_uses_wasm_blast_cap() -> None:
    plan = _ebpf_plan(blast_radius=BlastRadius(namespace="staging", max_replicas_pct=25))
    with pytest.raises(RefereeValidationError, match="blast radius"):
        validate_plan_for_execution(plan, enforce_freeze=False)


@pytest.mark.asyncio
async def test_correlator_includes_ebpf_metrics() -> None:
    correlator = ObservabilityCorrelator()
    plan = _ebpf_plan()
    evidence = await correlator.build_evidence(
        "exp-ebpf-2",
        plan,
        baseline={"checkout_error_rate": 0.01},
        window_start=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        window_end=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        force_simulate=True,
    )
    assert evidence.ebpf_metrics
    assert evidence.ebpf_metrics.get("fault_type") == "network_latency"
    assert any("eBPF" in line for line in evidence.correlations)
