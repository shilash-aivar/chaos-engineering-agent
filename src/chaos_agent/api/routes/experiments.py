from fastapi import APIRouter

from chaos_agent.models import ExperimentPlan, ExperimentRecord, ExperimentState

router = APIRouter()


@router.post("", response_model=ExperimentRecord)
async def create_experiment(plan: ExperimentPlan) -> ExperimentRecord:
    """Submit an experiment plan — orchestrator picks up async."""
    return ExperimentRecord(id="exp-placeholder", plan=plan, state=ExperimentState.PENDING)


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str) -> dict[str, str]:
    return {"id": experiment_id, "state": "pending"}
