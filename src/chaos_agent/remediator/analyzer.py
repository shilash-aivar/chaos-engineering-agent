"""Rule-based findings from fault-window evidence."""

from __future__ import annotations

import uuid
from typing import Any

from chaos_agent.models import ExperimentPlan, Severity
from chaos_agent.observability.types import FaultWindowEvidence
from chaos_agent.remediator.models import RemediationFinding


def analyze_evidence_rules(
    *,
    experiment_id: str,
    plan: ExperimentPlan,
    evidence: FaultWindowEvidence,
    slo_breached: bool = False,
) -> list[RemediationFinding]:
    findings: list[RemediationFinding] = []

    for metric in evidence.metrics:
        if metric.delta_ratio is not None and metric.delta_ratio >= 2.0:
            findings.append(
                RemediationFinding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    severity=Severity.HIGH if metric.delta_ratio >= 3 else Severity.MEDIUM,
                    title=f"Metric degradation: {metric.name}",
                    scope="observability",
                    evidence=[
                        f"{metric.name} baseline={metric.baseline} peak={metric.during_peak} "
                        f"delta_ratio={metric.delta_ratio:.2f}",
                    ],
                    prescription=f"Add alert + runbook for {metric.name}; tune retry/circuit breaker on fault path",
                    target_path="observability/alerts.yaml",
                    artifact_type="config",
                    suggested_diff=f"# Alert when {metric.name} exceeds baseline × 2 for 2m",
                    verification=f"Re-run experiment; {metric.name} should stay within guard threshold",
                    experiment_id=experiment_id,
                    source="rules",
                ),
            )

    for log in evidence.logs:
        if log.error_count >= 5:
            findings.append(
                RemediationFinding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    severity=Severity.HIGH,
                    title=f"Error spike in {log.service}",
                    scope="app",
                    evidence=log.top_patterns[:3] or [f"{log.error_count} errors during fault window"],
                    prescription=f"Harden error handling and timeouts on {log.service}",
                    target_path=f"src/{log.service}/handlers.py",
                    artifact_type="code",
                    suggested_diff="# Add bounded retry + structured error logging",
                    verification="Fault window logs should not show repeated stack traces",
                    experiment_id=experiment_id,
                    source="rules",
                ),
            )

    for trace in evidence.traces:
        if trace.error_spans > 0:
            findings.append(
                RemediationFinding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    severity=Severity.MEDIUM,
                    title=f"Trace errors on {trace.path}",
                    scope="app",
                    evidence=[f"{trace.error_spans} error spans across {trace.trace_count} traces"],
                    prescription="Add span attributes and dependency timeout on critical path",
                    target_path=f"observability/traces/{trace.path.replace('/', '-')}.yaml",
                    artifact_type="config",
                    suggested_diff="# OTel: mark dependency failures as retriable where safe",
                    verification="Re-run experiment; error spans should drop on guarded path",
                    experiment_id=experiment_id,
                    source="rules",
                ),
            )

    if slo_breached:
        primary_fault = plan.faults[0] if plan.faults else None
        findings.insert(
            0,
            RemediationFinding(
                id=f"find-{uuid.uuid4().hex[:8]}",
                severity=Severity.CRITICAL,
                title="SLO breached during chaos experiment",
                scope="app",
                evidence=evidence.correlations[:3] or ["Steady-state guard aborted experiment"],
                prescription="Add circuit breaker, bulkhead, or dependency fallback for injected fault",
                target_path=f"k8s/{primary_fault.target if primary_fault else 'checkout'}-deployment.yaml",
                artifact_type="manifest",
                suggested_diff="# readinessProbe + PDB + retry policy on outbound deps",
                verification="Re-run same fault; guard should not breach within max duration",
                experiment_id=experiment_id,
                source="rules",
            ),
        )

    for line in plan.infra_evidence[:3]:
        if "no retry" in line or "no circuit breaker" in line:
            service = line.split(":")[0]
            findings.append(
                RemediationFinding(
                    id=f"find-{uuid.uuid4().hex[:8]}",
                    severity=Severity.MEDIUM,
                    title=f"Resilience gap: {service}",
                    scope="app",
                    evidence=[line],
                    prescription="Add retry with jitter and circuit breaker on outbound calls",
                    target_path=f"mesh/{service}-vs.yaml",
                    artifact_type="config",
                    suggested_diff="# Istio VirtualService retries + outlierDetection",
                    verification="Inject latency fault; error rate should remain bounded",
                    experiment_id=experiment_id,
                    source="rules",
                ),
            )

    return _dedupe(findings)


def _dedupe(findings: list[RemediationFinding]) -> list[RemediationFinding]:
    seen: set[str] = set()
    out: list[RemediationFinding] = []
    for f in findings:
        key = f"{f.title}:{f.scope}"
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out[:8]
