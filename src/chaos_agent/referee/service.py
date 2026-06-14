"""Referee agent service — validation, scoring export, regression."""

from __future__ import annotations

from typing import Any

from chaos_agent.models import ExperimentPlan, ExperimentState
from chaos_agent.platform.regression_service import list_regression_suites
from chaos_agent.referee.freeze_calendar import active_freeze_reason, get_freeze_windows
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository
from chaos_agent.storage.repositories.regression import RegressionRepository


async def validate_experiment_plan(
    plan: ExperimentPlan,
    *,
    enforce_freeze: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        validate_plan_for_execution(plan, enforce_freeze=enforce_freeze)
        passed = True
    except RefereeValidationError as exc:
        passed = False
        errors.append(str(exc))

    freeze = active_freeze_reason()
    return {
        "passed": passed,
        "errors": errors,
        "freeze_active": freeze is not None,
        "freeze_reason": freeze,
    }


async def _count_pending_approvals() -> int:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        rows = await repo.list_all()
        return sum(1 for r in rows if r.state == ExperimentState.AWAITING_APPROVAL.value)


async def referee_status() -> dict[str, Any]:
    freeze = active_freeze_reason()
    suites = await list_regression_suites()
    pending = await _count_pending_approvals()
    return {
        "freeze": {
            "blocked": freeze is not None,
            "reason": freeze,
            "windows": get_freeze_windows(),
        },
        "regression_suites": len(suites),
        "pending_approvals": pending,
    }


async def export_equilibrium_round(campaign_id: str, round_num: int) -> dict[str, Any]:
    """Persist equilibrium round as regression suite."""
    from chaos_agent.storage.repositories.campaign import CampaignRepository

    factory = get_session_factory()
    async with factory() as session:
        camp_repo = CampaignRepository(session)
        detail = await camp_repo.get_campaign(campaign_id)
        if detail is None:
            return {"exported": False, "message": "Campaign not found"}
        round_data = next((r for r in detail.rounds if r.round == round_num), None)
        if round_data is None:
            return {"exported": False, "message": "Round not found"}
        if round_data.outcome != "draw":
            return {"exported": False, "message": "Only equilibrium (draw) rounds export"}

        payload = {
            "attack": round_data.attack.model_dump(),
            "defense": round_data.defense.model_dump(),
            "outcome": round_data.outcome,
            "referee_note": round_data.referee_note,
        }
        reg_repo = RegressionRepository(session)
        row = await reg_repo.save_suite(
            name=f"{detail.name} round {round_num} equilibrium",
            source="red_blue",
            payload=payload,
            campaign_id=campaign_id,
            round_num=round_num,
            tests=1,
            passing=1,
        )

    return {"exported": True, "suite": RegressionRepository.to_dict(row)}
