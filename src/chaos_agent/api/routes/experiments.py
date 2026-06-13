from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chaos_agent.composer.rules import compose_from_scenario
from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.models import ExperimentPlan, ExperimentState
from chaos_agent.orchestrator.engine import get_engine
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()


class ComposeRequest(BaseModel):
    scenario: str
    namespace: str = "staging"


class ComposeResponse(BaseModel):
    plan: ExperimentPlan
    summary: str


@router.get("")
async def list_experiments() -> list[dict]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        rows = await repo.list_all()
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
    try:
        validate_plan(plan)
    except SafetyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.create(plan)
        summary = repo.summary_dict(row)

    get_engine().start(row.id)
    return summary


@router.post("/compose", response_model=ComposeResponse)
async def compose_scenario(body: ComposeRequest) -> ComposeResponse:
    plan, summary = await compose_from_scenario(body.scenario, body.namespace)
    try:
        validate_plan(plan)
    except SafetyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ComposeResponse(plan=plan, summary=summary)


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
