from fastapi import APIRouter

from chaos_agent.platform.infrastructure_service import get_infrastructure_rings
from chaos_agent.platform.regression_service import list_regression_suites
from chaos_agent.platform.twin_service import get_twin_analysis
from chaos_agent.referee.freeze_calendar import active_freeze_reason, get_freeze_windows

router = APIRouter()

REFEREE_SCORING = [
    {"metric": "Attack success", "weight": 25, "red": "Breach confirmed = +15", "blue": "Partial impact only"},
    {"metric": "Defense effectiveness", "weight": 25, "red": "Weak countermeasure", "blue": "Effective patch drafted"},
    {"metric": "Detection time", "weight": 15, "red": "Slow alert firing", "blue": "Guard caught breach <60s"},
    {"metric": "Recovery time", "weight": 20, "red": "MTTR > SLO", "blue": "Metrics at baseline <3min"},
    {"metric": "Remediation landed", "weight": 15, "red": "No fix opened", "blue": "PR/issue opened"},
]


@router.get("/scoring")
async def referee_scoring() -> dict:
    return {"weights": REFEREE_SCORING}

@router.get("/freeze")
async def referee_freeze() -> dict:
    reason = active_freeze_reason()
    return {
        "windows": get_freeze_windows(),
        "active_reason": reason,
        "blocked": reason is not None,
    }


@router.get("/infrastructure")
async def infrastructure_rings(namespace: str = "staging") -> dict:
    return await get_infrastructure_rings(namespace)


@router.get("/twin")
async def digital_twin(namespace: str = "staging", fault_target: str = "payments-api") -> dict:
    return await get_twin_analysis(namespace, fault_target=fault_target)


@router.get("/regression")
async def regression_suites() -> dict:
    suites = await list_regression_suites()
    return {"suites": suites}
