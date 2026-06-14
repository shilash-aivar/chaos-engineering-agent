"""Helpers for async experiment dispatch."""

from __future__ import annotations

import re

from chaos_agent.config import get_settings
from chaos_agent.models import ExperimentPlan


def plan_duration_minutes(plan: ExperimentPlan) -> int:
    total = 0
    for fault in plan.faults:
        if fault.executor.value != "k6":
            continue
        duration = str(fault.params.get("duration", "5m"))
        match = re.match(r"(\d+)(m|h|s)", duration)
        if not match:
            continue
        value, unit = int(match.group(1)), match.group(2)
        if unit == "h":
            total += value * 60
        elif unit == "m":
            total += value
        elif unit == "s":
            total += max(1, value // 60)
    return total


def should_run_async(plan: ExperimentPlan) -> bool:
    settings = get_settings()
    if not settings.use_celery:
        return False
    if plan_duration_minutes(plan) >= settings.celery_long_duration_minutes:
        return True
    return any(f.type == "soak" for f in plan.faults)
