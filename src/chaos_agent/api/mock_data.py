"""Seed data for UI development until collectors and orchestrator are wired."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from chaos_agent.models import (
    BlastRadius,
    ExperimentPlan,
    ExperimentSource,
    ExperimentState,
    Fault,
    FaultExecutor,
    RollbackSpec,
    Target,
)

NOW = datetime.now(timezone.utc)


def _ts(minutes_ago: int = 0) -> str:
    return (NOW - timedelta(minutes=minutes_ago)).isoformat()


SAMPLE_PLAN = ExperimentPlan(
    name="checkout-inventory-latency",
    hypothesis="Checkout degrades when inventory API latency exceeds 500ms under load",
    source=ExperimentSource.HYBRID,
    targets=[Target(service="checkout", namespace="staging")],
    faults=[
        Fault(
            executor=FaultExecutor.CHAOS_MESH,
            type="network_latency",
            target="inventory-api",
            params={"latency_ms": 500},
        ),
        Fault(executor=FaultExecutor.K6, type="load", target="checkout", params={"vus": 50}),
    ],
    infra_evidence=[
        "checkout→inventory: no retry in VirtualService",
        "inventory-api: 2 replicas, no PDB",
        "RDS payments-db: connection pool size 10",
    ],
    blast_radius=BlastRadius(namespace="staging", environment="staging"),
    watch_metrics=["checkout_error_rate", "checkout_p99", "inventory_upstream_errors"],
    rollback=RollbackSpec(type="delete_chaos_crd", ttl_seconds=300),
)

_EXPERIMENTS: list[dict[str, Any]] = [
    {
        "id": "exp-001",
        "name": "checkout-inventory-latency",
        "hypothesis": SAMPLE_PLAN.hypothesis,
        "state": ExperimentState.COMPLETE,
        "source": ExperimentSource.HYBRID,
        "namespace": "staging",
        "environment": "staging",
        "created_at": _ts(120),
        "red_score": 68,
        "blue_score": 42,
        "plan": SAMPLE_PLAN,
        "timeline": [
            {"at": _ts(118), "event": "Baseline captured", "detail": "5 min Prometheus window"},
            {"at": _ts(115), "event": "Fault injected", "detail": "network_latency 500ms on inventory-api"},
            {"at": _ts(110), "event": "SLO breach", "detail": "checkout error rate 4.2%"},
            {"at": _ts(109), "event": "Auto rollback", "detail": "Chaos CRD deleted"},
            {"at": _ts(105), "event": "Remediation", "detail": "3 findings, 3 GitHub issues"},
        ],
        "findings_count": 3,
    },
    {
        "id": "exp-002",
        "name": "payments-pod-kill",
        "hypothesis": "Payments survives random pod termination with current probes",
        "state": ExperimentState.RUNNING,
        "source": ExperimentSource.RED_AGENT,
        "namespace": "staging",
        "environment": "staging",
        "created_at": _ts(15),
        "red_score": None,
        "blue_score": None,
        "plan": ExperimentPlan(
            name="payments-pod-kill",
            hypothesis="Payments survives random pod termination with current probes",
            source=ExperimentSource.RED_AGENT,
            targets=[Target(service="payments-api", namespace="staging")],
            faults=[
                Fault(executor=FaultExecutor.CHAOS_MESH, type="pod_kill", target="payments-api"),
            ],
            infra_evidence=["payments-api: no readiness probe", "PriorityClass not set"],
            blast_radius=BlastRadius(namespace="staging", environment="staging"),
            watch_metrics=["payments_error_rate", "payments_p99"],
            rollback=RollbackSpec(type="delete_chaos_crd"),
        ),
        "timeline": [
            {"at": _ts(14), "event": "Red agent plan approved"},
            {"at": _ts(12), "event": "Fault injected", "detail": "pod_kill 30% replicas"},
        ],
        "findings_count": 0,
    },
    {
        "id": "exp-003",
        "name": "rds-failover-rto",
        "hypothesis": "Checkout RTO stays under 60s on RDS failover",
        "state": ExperimentState.AWAITING_APPROVAL,
        "source": ExperimentSource.LLM,
        "namespace": "staging",
        "environment": "staging",
        "created_at": _ts(5),
        "plan": ExperimentPlan(
            name="rds-failover-rto",
            hypothesis="Checkout RTO stays under 60s on RDS failover",
            source=ExperimentSource.LLM,
            targets=[Target(service="checkout", namespace="staging")],
            faults=[
                Fault(executor=FaultExecutor.AWS_FIS, type="rds_failover", target="payments-db"),
            ],
            infra_evidence=["RDS payments-db: Multi-AZ=false", "No circuit breaker on DB pool"],
            blast_radius=BlastRadius(namespace="staging", environment="staging"),
            watch_metrics=["checkout_error_rate", "db_connection_errors"],
            rollback=RollbackSpec(type="aws_fis_stop"),
        ),
        "timeline": [{"at": _ts(5), "event": "Awaiting Slack approval"}],
        "findings_count": 0,
    },
]

_POSTURE_GAPS = [
    {
        "id": "gap-1",
        "scope": "k8s",
        "severity": "critical",
        "service": "payments-api",
        "rule": "critical-pods-priority-class",
        "message": "Critical tier deployment has no PriorityClass — evicted first under node pressure",
        "remediation": "Create chaos-critical PriorityClass and patch deployment",
    },
    {
        "id": "gap-2",
        "scope": "k8s",
        "severity": "high",
        "service": "checkout",
        "rule": "critical-deployment-probes",
        "message": "Missing readiness probe — ALB routes traffic to terminating pods",
        "remediation": "Add httpGet /health readiness probe",
    },
    {
        "id": "gap-3",
        "scope": "aws",
        "severity": "critical",
        "service": "payments-db",
        "rule": "critical-rds-multi-az",
        "message": "RDS instance is single-AZ",
        "remediation": "Terraform PR: multi_az = true",
    },
    {
        "id": "gap-4",
        "scope": "aws",
        "severity": "high",
        "service": "order-events",
        "rule": "critical-sqs-dlq",
        "message": "Critical SQS queue has no dead-letter queue",
        "remediation": "Add DLQ and alarm on oldest message age",
    },
]

_CAMPAIGNS: list[dict[str, Any]] = [
    {
        "id": "camp-001",
        "name": "checkout-game-day",
        "state": "active",
        "round": 2,
        "max_rounds": 3,
        "red_score": 61,
        "blue_score": 54,
        "leader": "red",
        "last_round_at": _ts(30),
    },
    {
        "id": "camp-002",
        "name": "payments-hardening",
        "state": "complete",
        "round": 3,
        "max_rounds": 3,
        "red_score": 38,
        "blue_score": 82,
        "leader": "blue",
        "last_round_at": _ts(2880),
    },
]


def list_experiment_summaries() -> list[dict[str, Any]]:
    return [
        {k: v for k, v in exp.items() if k not in ("plan", "timeline", "findings_count")}
        for exp in _EXPERIMENTS
    ]


def get_experiment(experiment_id: str) -> Optional[dict[str, Any]]:
    for exp in _EXPERIMENTS:
        if exp["id"] == experiment_id:
            return exp
    return None


def add_experiment(plan: ExperimentPlan) -> dict[str, Any]:
    exp_id = f"exp-{len(_EXPERIMENTS) + 1:03d}"
    record = {
        "id": exp_id,
        "name": plan.name,
        "hypothesis": plan.hypothesis,
        "state": ExperimentState.PENDING,
        "source": plan.source,
        "namespace": plan.blast_radius.namespace,
        "environment": plan.blast_radius.environment,
        "created_at": _ts(0),
        "red_score": None,
        "blue_score": None,
        "plan": plan,
        "timeline": [{"at": _ts(0), "event": "Experiment queued"}],
        "findings_count": 0,
    }
    _EXPERIMENTS.insert(0, record)
    return {k: v for k, v in record.items() if k not in ("plan", "timeline", "findings_count")}


def compose_plan(scenario: str, namespace: str) -> tuple[ExperimentPlan, str]:
    plan = SAMPLE_PLAN.model_copy(
        update={
            "hypothesis": scenario,
            "name": scenario[:48].lower().replace(" ", "-").strip("-"),
            "source": ExperimentSource.HYBRID,
            "blast_radius": BlastRadius(namespace=namespace, environment="staging"),
            "targets": [Target(service="checkout", namespace=namespace)],
        },
    )
    summary = (
        "LLM grounded your scenario on the staging service graph. "
        "Detected unprotected checkout→inventory edge and recommended latency + load faults."
    )
    return plan, summary


def dashboard_stats() -> dict[str, Any]:
    running = sum(1 for e in _EXPERIMENTS if e["state"] == ExperimentState.RUNNING)
    return {
        "experiments_total": len(_EXPERIMENTS),
        "experiments_running": running,
        "avg_resilience_score": 67,
        "posture_gaps": len(_POSTURE_GAPS),
        "red_blue_campaigns": len(list_campaigns()),
        "last_experiment_at": _EXPERIMENTS[0]["created_at"] if _EXPERIMENTS else None,
    }


def posture_scan() -> dict[str, Any]:
    return {"gaps": _POSTURE_GAPS, "scanned_at": _ts(0)}


def list_campaigns() -> list[dict[str, Any]]:
    import asyncio

    from chaos_agent.red_blue import campaign as rb

    return asyncio.run(rb.list_campaigns())


def start_campaign(name: str) -> dict[str, Any]:
    import asyncio

    from chaos_agent.red_blue import campaign as rb

    return asyncio.run(rb.start_campaign(name))


def abort_experiment(experiment_id: str) -> bool:
    exp = get_experiment(experiment_id)
    if not exp:
        return False
    exp["state"] = ExperimentState.ABORTING
    exp["timeline"].append({"at": _ts(0), "event": "Abort requested", "detail": "Rollback triggered"})
    exp["state"] = ExperimentState.COMPLETE
    exp["timeline"].append({"at": _ts(0), "event": "Rollback complete"})
    return True
