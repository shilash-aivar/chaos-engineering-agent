from fastapi import APIRouter

from chaos_agent.platform.policies_service import (
    get_executor_allowlist,
    get_policy_yaml,
    get_posture_rules,
    get_runtime_policies,
)

router = APIRouter()


@router.get("/runtime")
async def runtime_policies() -> dict:
    return {
        "policies": get_runtime_policies(),
        "executors": get_executor_allowlist(),
    }


@router.get("/posture-rules")
async def posture_rules() -> dict:
    return {"rules": get_posture_rules()}


@router.get("/yaml")
async def policy_yaml() -> dict:
    return {"yaml": get_policy_yaml()}
