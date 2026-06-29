"""Composer agent — full compose with pre-mortem, twin, and feedback loop."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.composer.feedback import load_feedback_context, load_latest_feedback
from chaos_agent.composer.llm import compose_with_llm
from chaos_agent.composer.premortem import generate_pre_mortem
from chaos_agent.composer.rules import compose_from_scenario
from chaos_agent.models import ExperimentPlan
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.context_agent import ContextAgentRepository


async def compose_scenario(
    scenario: str,
    namespace: str = "staging",
    *,
    environment: str = "staging",
    prior_feedback: Optional[dict[str, Any]] = None,
    context_agent: Optional[dict[str, Any]] = None,
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
        context_agent=context_agent,
        environment=environment,
    )
    if llm_result is not None:
        plan, summary = llm_result
        return plan, summary, "llm"

    plan, summary = await compose_from_scenario(scenario, namespace)
    if feedback and feedback.get("slo_breached"):
        summary = f"{summary} (prior run {feedback.get('experiment_id')} breached SLO — rules fallback)"
    if context_agent:
        focus = ", ".join(context_agent.get("recommended_chaos_focus", [])[:2])
        if focus:
            summary = f"{summary} Context-agent focus: {focus}."
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

    context_agent = await load_latest_context_agent(namespace)

    plan, summary, mode = await compose_scenario(
        scenario,
        namespace,
        environment=environment,
        prior_feedback=prior_feedback,
        context_agent=context_agent,
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
        "context_agent": context_agent,
        "llm_grounded": mode == "llm",
    }


async def load_latest_context_agent(namespace: str = "staging") -> Optional[dict[str, Any]]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextAgentRepository(session)
        row = await repo.latest(namespace)
        if row is None:
            return None
        return ContextAgentRepository.row_to_result(row)
