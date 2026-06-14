"""Chaos DNA — per-service resilience profiles from experiments and campaigns."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select

from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.orm import CampaignRow, ExperimentRow
from chaos_agent.storage.repositories.experiments import ExperimentRepository
from chaos_agent.storage.repositories.regression import RegressionRepository


async def _compute_mttr_seconds(experiment_ids: list[str]) -> int | None:
    if not experiment_ids:
        return None
    factory = get_session_factory()
    durations: list[float] = []
    async with factory() as session:
        repo = ExperimentRepository(session)
        for exp_id in experiment_ids[:30]:
            row = await repo.get(exp_id)
            if row is None or row.completed_at is None:
                continue
            events = await repo.get_events(exp_id)
            fault_at = None
            for event in events:
                if event.event in ("Fault injected", "Load test started", "AWS FIS started"):
                    fault_at = event.created_at
                    break
            if fault_at is None:
                continue
            end = row.completed_at
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            if fault_at.tzinfo is None:
                fault_at = fault_at.replace(tzinfo=timezone.utc)
            durations.append((end - fault_at).total_seconds())
    if not durations:
        return None
    return int(sum(durations) / len(durations))


def _weekly_history(experiments: list[ExperimentRow], weeks: int = 8) -> list[dict[str, Any]]:
    if not experiments:
        return []
    now = datetime.now(timezone.utc)
    buckets: dict[str, list[int]] = defaultdict(list)
    for row in experiments:
        ts = row.completed_at or row.created_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        week_start = (ts - timedelta(days=ts.weekday())).strftime("%Y-%m-%d")
        score = 75 if row.state == "complete" and not row.slo_breached else 55 if row.state == "complete" else 45
        buckets[week_start].append(score)
    history = []
    for i in range(weeks):
        week_dt = now - timedelta(weeks=weeks - i - 1)
        key = (week_dt - timedelta(days=week_dt.weekday())).strftime("%Y-%m-%d")
        scores = buckets.get(key, [])
        history.append({"week": key, "score": int(sum(scores) / len(scores)) if scores else 0})
    return [h for h in history if h["score"] > 0] or history[-4:]


async def get_chaos_dna(namespace: str = "staging") -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        exp_result = await session.execute(
            select(ExperimentRow).where(ExperimentRow.namespace == namespace).order_by(
                ExperimentRow.created_at.desc(),
            ),
        )
        experiments = list(exp_result.scalars().all())

        camp_result = await session.execute(select(CampaignRow))
        campaigns = list(camp_result.scalars().all())

        reg_repo = RegressionRepository(session)
        regression_suites = await reg_repo.list_suites()

    service_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "experiments": 0,
            "completed": 0,
            "slo_breaches": 0,
            "faults_survived": set(),
            "weak_points": set(),
            "last_tested": None,
            "tier": "standard",
        },
    )

    completed_ids: list[str] = []
    for row in experiments:
        plan = ExperimentRepository.plan_from_row(row)
        for target in plan.targets:
            svc = target.service
            stats = service_stats[svc]
            stats["experiments"] += 1
            stats["tier"] = "critical" if svc in ("checkout", "payments-api") else "standard"
            if row.state == "complete":
                stats["completed"] += 1
                completed_ids.append(row.id)
                if not row.slo_breached:
                    for fault in plan.faults:
                        if fault.target:
                            stats["faults_survived"].add(fault.type)
                else:
                    stats["weak_points"].add("slo_breach")
            if row.slo_breached:
                stats["slo_breaches"] += 1
                stats["weak_points"].add("steady-state guard")
            ts = row.completed_at or row.created_at
            if stats["last_tested"] is None or ts > stats["last_tested"]:
                stats["last_tested"] = ts

    profiles = []
    for service, stats in sorted(service_stats.items()):
        completed = stats["completed"]
        total = stats["experiments"]
        breach_rate = stats["slo_breaches"] / total if total else 0
        score = max(40, min(95, 70 + completed * 3 - breach_rate * 20 - len(stats["weak_points"]) * 5))
        trend = "up" if completed >= 2 and not stats["weak_points"] else "down" if stats["weak_points"] else "flat"
        profiles.append(
            {
                "service": service,
                "tier": stats["tier"],
                "resilience_score": int(score),
                "faults_survived": sorted(stats["faults_survived"]) or ["pod_kill"],
                "weak_points": sorted(stats["weak_points"]) or ["not yet tested"],
                "last_tested": stats["last_tested"].isoformat() if stats["last_tested"] else "never",
                "trend": trend,
            },
        )

    empty_state = not profiles
    if empty_state:
        profiles = []

    org_score = int(sum(p["resilience_score"] for p in profiles) / len(profiles)) if profiles else 0
    history = _weekly_history(experiments)
    prior_scores = [h["score"] for h in history[:-1] if h["score"] > 0]
    current_scores = [h["score"] for h in history[-2:] if h["score"] > 0]
    if prior_scores and current_scores:
        delta = int(sum(current_scores) / len(current_scores) - sum(prior_scores) / len(prior_scores))
        org_delta = f"{delta:+d} vs prior weeks"
    else:
        org_delta = "no baseline yet"

    mttr = await _compute_mttr_seconds(completed_ids)
    regression_passing = sum(1 for s in regression_suites if s.passing >= s.tests) if regression_suites else 0

    return {
        "org_score": org_score,
        "org_delta": org_delta,
        "faults_survived_avg": round(
            sum(len(p["faults_survived"]) for p in profiles) / max(len(profiles), 1),
            1,
        )
        if profiles
        else 0,
        "mttr_seconds": mttr,
        "regression_suites_passing": regression_passing,
        "profiles": profiles,
        "history": history or [],
        "namespace": namespace,
        "empty_state": empty_state,
        "campaign_rounds": sum(c.round for c in campaigns),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
