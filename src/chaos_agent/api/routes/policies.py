from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chaos_agent.platform.policies_service import (
    get_executor_allowlist,
    get_policy_yaml,
    get_posture_rules,
    get_runtime_policies,
    save_policy_yaml,
)

router = APIRouter()


class PolicyYamlUpdate(BaseModel):
    yaml: str


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
    content = get_policy_yaml()
    return {"yaml": content, "editable": True}


@router.put("/yaml")
async def update_policy_yaml(body: PolicyYamlUpdate) -> dict:
    try:
        result = save_policy_yaml(body.yaml)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
