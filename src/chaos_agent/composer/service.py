"""Composer agent — full compose with pre-mortem, twin, and feedback loop."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.composer.feedback import load_feedback_context, load_latest_feedback
from chaos_agent.composer.llm import compose_with_llm
from chaos_agent.composer.premortem import generate_pre_mortem
from chaos_agent.composer.rules import compose_from_scenario
from chaos_agent.models import ExperimentPlan
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution


async def compose_scenario(
    scenario: str,
    namespace: str = "staging",
    *,
    environment: str = "staging",
    prior_feedback: Optional[dict[str, Any]] = None,
    use_latest_feedback: bool = False,
) -> tuple[ExperimentPlan, str, str]:
    """Return plan, summary, and composer mode (llm | rules)."""
    feedback = prior_feedback
    if use_latest_feedback and feedback is None:
        feedback = await load_latest_feedback(namespace)

    llm_result = await compose_with_llm(
        scenario,
        namespace,
        prior_feedback=feedback,
        environment=environment,
    )
    if llm_result is not None:
        plan, summary = llm_result
        return plan, summary, "llm"

    plan, summary = await compose_from_scenario(scenario, namespace)
    if feedback and feedback.get("slo_breached"):
        summary = f"{summary} (prior run {feedback.get('experiment_id')} breached SLO — rules fallback)"
    return plan, summary, "rules"


async def compose_full(
    scenario: str,
    namespace: str = "staging",
    *,
    environment: str = "staging",
    enforce_referee: bool = True,
    prior_experiment_id: Optional[str] = None,
    use_latest_feedback: bool = False,
) -> dict[str, Any]:
    """Compose plan + pre-mortem + referee validation."""
    prior_feedback = None
    if prior_experiment_id:
        prior_feedback = await load_feedback_context(prior_experiment_id)
    elif use_latest_feedback:
        prior_feedback = await load_latest_feedback(namespace)

    plan, summary, mode = await compose_scenario(
        scenario,
        namespace,
        environment=environment,
        prior_feedback=prior_feedback,
    )
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
        "prior_feedback": prior_feedback,
        "llm_grounded": mode == "llm",
    }
