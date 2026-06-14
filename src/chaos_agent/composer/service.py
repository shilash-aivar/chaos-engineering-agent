"""Composer agent — full compose with pre-mortem and twin."""

from __future__ import annotations

from typing import Any

from chaos_agent.composer.llm import compose_with_llm
from chaos_agent.composer.premortem import generate_pre_mortem
from chaos_agent.composer.rules import compose_from_scenario
from chaos_agent.models import ExperimentPlan
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution


async def compose_scenario(
    scenario: str,
    namespace: str = "staging",
) -> tuple[ExperimentPlan, str, str]:
    """Return plan, summary, and composer mode (llm | rules)."""
    llm_result = await compose_with_llm(scenario, namespace)
    if llm_result is not None:
        plan, summary = llm_result
        return plan, summary, "llm"

    plan, summary = await compose_from_scenario(scenario, namespace)
    return plan, summary, "rules"


async def compose_full(
    scenario: str,
    namespace: str = "staging",
    *,
    enforce_referee: bool = True,
) -> dict[str, Any]:
    """Compose plan + pre-mortem + referee validation."""
    plan, summary, mode = await compose_scenario(scenario, namespace)
    referee_errors: list[str] = []
    referee_ok = True
    try:
        validate_plan_for_execution(plan, enforce_freeze=enforce_referee)
    except RefereeValidationError as exc:
        referee_ok = False
        referee_errors.append(str(exc))

    pre_mortem = await generate_pre_mortem(plan, namespace=namespace)
    return {
        "plan": plan,
        "summary": summary,
        "composer": mode,
        "pre_mortem": pre_mortem,
        "referee": {"passed": referee_ok, "errors": referee_errors},
        "twin_preview": pre_mortem.get("twin_preview"),
    }
