from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.orchestrator.engine import get_engine
from chaos_agent.platform.load_tests_service import find_scenario, get_catalog, scenario_to_plan
from chaos_agent.referee.validator import RefereeValidationError, validate_plan_for_execution
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()


class RunScenarioRequest(BaseModel):
    namespace: str = "staging"
    include_fault: bool = True
    pairing_id: str | None = None
    start: bool = True


@router.get("")
async def load_tests() -> dict:
    return get_catalog()


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> dict:
    scenario = find_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {scenario_id}")
    return scenario


@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: str, body: RunScenarioRequest | None = None) -> dict:
    req = body or RunScenarioRequest()
    try:
        plan = scenario_to_plan(
            scenario_id,
            namespace=req.namespace,
            include_fault=req.include_fault,
            pairing_id=req.pairing_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        validate_plan_for_execution(plan)
    except (SafetyValidationError, RefereeValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.create(plan)
        summary = repo.summary_dict(row)
        experiment_id = row.id
        await session.commit()

    started = False
    if req.start:
        await get_engine().start(experiment_id)
        started = True

    return {
        "experiment_id": experiment_id,
        "scenario_id": scenario_id,
        "plan": plan.model_dump(),
        "summary": summary,
        "started": started,
    }
