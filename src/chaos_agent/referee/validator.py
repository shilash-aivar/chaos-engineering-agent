"""Referee plan gate — deterministic policy beyond composer safety."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.models import ExperimentPlan
from chaos_agent.referee.freeze_calendar import active_freeze_reason


class RefereeValidationError(SafetyValidationError):
    pass


def validate_plan_for_execution(
    plan: ExperimentPlan,
    *,
    now: Optional[datetime] = None,
    enforce_freeze: bool = True,
    skip_production_gate: bool = False,
) -> None:
    """Composer safety + optional freeze calendar gate."""
    validate_plan(plan)

    if not skip_production_gate and plan.blast_radius.environment == "production":
        raise RefereeValidationError("production experiments require explicit referee approval")

    if enforce_freeze:
        reason = active_freeze_reason()
        if reason:
            raise RefereeValidationError(reason)

    for fault in plan.faults:
        if fault.type == "pod_kill" and plan.blast_radius.max_replicas_pct > 20:
            raise RefereeValidationError(
                f"pod_kill with blast radius {plan.blast_radius.max_replicas_pct}% exceeds referee cap 20%",
            )
