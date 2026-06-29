from __future__ import annotations

from typing import Any, Optional

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chaos_agent.composer.service import compose_full, compose_scenario
from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.config import get_settings
from chaos_agent.models import ExperimentPlan, ExperimentState
from chaos_agent.orchestrator.engine import get_engine
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()
logger = logging.getLogger(__name__)


class ComposeRequest(BaseModel):
    scenario: str
    namespace: str = "staging"


class ComposeFullRequest(BaseModel):
    scenario: str
    namespace: str = "staging"
    environment: str = "staging"
    enforce_referee: bool = True
    prior_experiment_id: Optional[str] = None
    use_latest_feedback: bool = False


class ComposeResponse(BaseModel):
    plan: ExperimentPlan
    summary: str
    composer: str = "rules"


class ComposeFullResponse(BaseModel):
    plan: ExperimentPlan
    summary: str
    composer: str = "rules"
    pre_mortem: dict[str, Any]
    referee: dict[str, Any]
    twin_preview: Optional[dict[str, Any]] = None
    prior_feedback: Optional[dict[str, Any]] = None
    llm_grounded: bool = False


@router.get("")
async def list_experiments(namespace: Optional[str] = None) -> list[dict]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        rows = await repo.list_all(namespace=namespace)
        return [repo.summary_dict(r) for r in rows]


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return await repo.detail_dict(row)


@router.post("")
async def create_experiment(plan: ExperimentPlan) -> dict:
    settings = get_settings()
    needs_approval = (
        settings.require_approval_production
        and plan.blast_radius.environment == "production"
    )
    try:
        validate_plan_for_execution(plan, skip_production_gate=needs_approval)
    except (SafetyValidationError, RefereeValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.create(plan)
        if needs_approval:
            await repo.set_state(row.id, ExperimentState.AWAITING_APPROVAL)
            await repo.add_event(row.id, "Awaiting approval", "Production experiment needs referee sign-off")
            await session.commit()
            notification_sent = False
            try:
                from chaos_agent.integrations.slack.client import SlackClient

                slack = SlackClient()
                if slack.available:
                    await slack.notify_approval_needed(
                        row.id,
                        plan.name,
                        plan.blast_radius.environment,
                        api_base=settings.api_public_url,
                    )
                    notification_sent = True
            except Exception as exc:
                logger.warning("slack_approval_notify_failed", extra={"experiment_id": row.id, "error": str(exc)})
            summary = repo.summary_dict(await repo.get(row.id))
            summary["notification_sent"] = notification_sent
            return summary

        experiment_id = row.id
        summary = repo.summary_dict(row)

    from chaos_agent.orchestrator.dispatch import should_run_async
    from chaos_agent.workers.tasks import dispatch_experiment

    if should_run_async(plan):
        queued, via = dispatch_experiment(experiment_id)
        if queued:
            async with factory() as session:
                repo = ExperimentRepository(session)
                await repo.add_event(experiment_id, "Dispatched async", f"via {via}")
                await session.commit()
            return {**summary, "dispatch": via}
    await get_engine().start(experiment_id)
    return summary


@router.post("/compose", response_model=ComposeResponse)
async def compose_scenario_route(body: ComposeRequest) -> ComposeResponse:
    plan, summary, mode = await compose_scenario(body.scenario, body.namespace)
    try:
        validate_plan(plan)
    except SafetyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ComposeResponse(plan=plan, summary=summary, composer=mode)


@router.post("/compose-full", response_model=ComposeFullResponse)
async def compose_full_route(body: ComposeFullRequest) -> ComposeFullResponse:
    result = await compose_full(
        body.scenario,
        body.namespace,
        environment=body.environment,
        enforce_referee=body.enforce_referee,
        prior_experiment_id=body.prior_experiment_id,
        use_latest_feedback=body.use_latest_feedback,
    )
    if not result["referee"]["passed"]:
        raise HTTPException(status_code=400, detail="; ".join(result["referee"]["errors"]))
    return ComposeFullResponse(
        plan=result["plan"],
        summary=result["summary"],
        composer=result["composer"],
        pre_mortem=result["pre_mortem"],
        referee=result["referee"],
        twin_preview=result.get("twin_preview"),
        prior_feedback=result.get("prior_feedback"),
        llm_grounded=result.get("llm_grounded", False),
    )


@router.post("/{experiment_id}/approve")
async def approve_experiment(experiment_id: str) -> dict[str, str]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if row.state != ExperimentState.AWAITING_APPROVAL.value:
            raise HTTPException(status_code=409, detail=f"Experiment is {row.state}, not awaiting approval")

    ok = await get_engine().approve(experiment_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Referee rejected plan or approval failed")
    return {"status": "approved", "experiment_id": experiment_id}


@router.post("/{experiment_id}/abort")
async def abort_experiment(experiment_id: str) -> dict[str, str]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if row.state in (ExperimentState.COMPLETE.value, ExperimentState.FAILED.value):
            raise HTTPException(status_code=409, detail=f"Experiment already {row.state}")

    ok = await get_engine().request_abort(experiment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"status": "abort_requested"}
