"""Red vs Blue campaign API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chaos_agent.red_blue import campaign as rb
from chaos_agent.security.frameworks.registry import get_framework, list_frameworks
from chaos_agent.security.generator import generate_attack_plan

router = APIRouter()


class StartCampaignRequest(BaseModel):
    name: str
    namespace: str = "staging"
    include_security: bool = False
    security_mix_pct: int = Field(default=50, ge=0, le=100)
    attack_framework_id: Optional[str] = None
    attack_category_ids: list[str] = Field(default_factory=list)
    attack_plan_id: Optional[str] = None


class GenerateAttackPlanRequest(BaseModel):
    framework_id: str
    namespace: str = "staging"
    category_ids: list[str] = Field(default_factory=list)
    target_services: dict[str, str] = Field(default_factory=dict)


@router.get("/campaigns")
async def list_campaigns() -> list[dict]:
    return await rb.list_campaigns()


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str) -> dict:
    detail = await rb.get_campaign(campaign_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return detail.model_dump(mode="json")


@router.post("/campaigns")
async def start_campaign(body: StartCampaignRequest) -> dict:
    return await rb.start_campaign(
        body.name,
        namespace=body.namespace,
        include_security=body.include_security,
        security_mix_pct=body.security_mix_pct,
        attack_framework_id=body.attack_framework_id,
        attack_category_ids=body.attack_category_ids or None,
        attack_plan_id=body.attack_plan_id,
    )


@router.post("/campaigns/{campaign_id}/round")
async def run_round(campaign_id: str) -> dict:
    result = await rb.run_round(campaign_id)
    if result is None:
        camp = await rb.get_campaign(campaign_id)
        if camp is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
        raise HTTPException(status_code=409, detail="Campaign complete or cannot advance")
    return result


@router.post("/campaigns/{campaign_id}/rounds/{round_num}/remediate")
async def remediate_round(campaign_id: str, round_num: int) -> dict:
    try:
        return await rb.remediate_round(campaign_id, round_num)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/campaigns/{campaign_id}/rounds/{round_num}/verify")
async def verify_round(campaign_id: str, round_num: int) -> dict:
    try:
        return await rb.verify_round_remediation(campaign_id, round_num)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/security/attacks")
async def list_security_attacks() -> list[dict]:
    return rb.security_attack_catalog()


@router.get("/security/frameworks")
async def list_attack_frameworks() -> list[dict]:
    return [fw.model_dump(mode="json") for fw in list_frameworks()]


@router.get("/security/frameworks/{framework_id}")
async def get_attack_framework(framework_id: str) -> dict:
    fw = get_framework(framework_id)
    if fw is None:
        raise HTTPException(status_code=404, detail="Framework not found")
    return fw.model_dump(mode="json")


@router.post("/security/generate")
async def generate_security_attacks(body: GenerateAttackPlanRequest) -> dict:
    try:
        plan = generate_attack_plan(
            framework_id=body.framework_id,
            namespace=body.namespace,
            category_ids=body.category_ids or None,
            target_services=body.target_services or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    plan_id = await rb.store_attack_plan(plan)
    payload = plan.model_dump(mode="json")
    payload["plan_id"] = plan_id
    return payload


@router.get("/security/plans/{plan_id}")
async def get_attack_plan(plan_id: str) -> dict:
    plan = await rb.get_attack_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Attack plan not found")
    payload = plan.model_dump(mode="json")
    payload["plan_id"] = plan_id
    return payload
