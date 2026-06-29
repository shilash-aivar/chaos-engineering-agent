"""Agent runtime — per-agent APIs."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chaos_agent.blue.service import (
    defend_red_attack,
    get_blue_suggestions,
    remediate_defense,
    verify_defense,
)
from chaos_agent.composer.premortem import generate_pre_mortem
from chaos_agent.composer.service import compose_full, compose_scenario
from chaos_agent.config import get_settings
from chaos_agent.context.agent.loop import run_context_agent
from chaos_agent.context.types import ContextGap
from chaos_agent.llm.client import get_llm_client
from chaos_agent.models import ExperimentPlan
from chaos_agent.red.service import execute_red_attack, plan_red_attack
from chaos_agent.referee.service import (
    export_equilibrium_round,
    referee_status,
    validate_experiment_plan,
)
from chaos_agent.remediator.templates.runbook import render_runbook
from chaos_agent.remediator.verify import verify_finding
from chaos_agent.security.types import BlueDefense, RedAttack
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.context_agent import ContextAgentRepository
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()


@router.get("/status")
async def agent_status() -> dict:
    settings = get_settings()
    llm = get_llm_client()
    ref = await referee_status()
    return {
        "llm_enabled": settings.llm_enabled,
        "llm_available": llm.available,
        "llm_connection": (
            "connected"
            if llm.available
            else "disabled"
            if not settings.llm_enabled
            else "missing_api_key"
        ),
        "model": settings.anthropic_model if llm.available else None,
        "agents": {
            "composer": "llm+rules" if llm.available else "rules",
            "remediator": "llm+rules" if llm.available else "rules",
            "red": "llm+rules" if llm.available else "rules",
            "blue": "llm+rules" if llm.available else "rules",
            "referee": "deterministic",
            "context": "llm+tools" if llm.available else "tools",
        },
        "referee": ref,
    }


class ComposeFullRequest(BaseModel):
    scenario: str
    namespace: str = "staging"
    environment: str = "staging"
    enforce_referee: bool = True
    prior_experiment_id: Optional[str] = None
    use_latest_feedback: bool = False


class RedPlanRequest(BaseModel):
    round_num: int = 1
    namespace: str = "staging"
    include_security: bool = False
    security_mix_pct: int = 50
    prior_techniques: list[str] = Field(default_factory=list)
    use_llm: bool = True


class RedExecuteRequest(BaseModel):
    attack: RedAttack
    namespace: str = "staging"


class BlueSuggestRequest(BaseModel):
    gaps: list[ContextGap]
    use_llm: bool = True


class BlueDefendRequest(BaseModel):
    attack: RedAttack
    namespace: str = "staging"
    posture_gaps: Optional[list[dict[str, Any]]] = None
    evidence_summary: Optional[list[str]] = None
    use_llm: bool = True


class BlueVerifyRequest(BaseModel):
    attack: RedAttack
    defense: BlueDefense
    namespace: str = "staging"
    re_inject: bool = True


class RefereeValidateRequest(BaseModel):
    plan: ExperimentPlan
    enforce_freeze: bool = True


class RefereeExportRequest(BaseModel):
    campaign_id: str
    round_num: int


class PremortemRequest(BaseModel):
    plan: ExperimentPlan
    namespace: str = "staging"


class ContextUnderstandRequest(BaseModel):
    problem_statement: str = ""
    namespace: str = "staging"
    context_id: Optional[str] = None
    service: Optional[str] = None
    max_iterations: int = 8
    persist: bool = True


@router.post("/context/understand")
async def context_understand(body: ContextUnderstandRequest) -> dict[str, Any]:
    """Run the context agent loop: tools → LLM reasoning → infrastructure summary."""
    result = await run_context_agent(
        problem_statement=body.problem_statement,
        namespace=body.namespace,
        context_id=body.context_id,
        service=body.service,
        max_iterations=body.max_iterations,
    )
    if body.persist:
        factory = get_session_factory()
        async with factory() as session:
            repo = ContextAgentRepository(session)
            row = await repo.save_run(result, context_id=body.context_id)
            result["id"] = row.id
            result["created_at"] = row.created_at.isoformat()
    return result


@router.get("/context/runs")
async def context_agent_runs(namespace: str = "staging", limit: int = 20) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextAgentRepository(session)
        rows = await repo.list_runs(namespace, limit=limit)
        return {
            "runs": [
                {
                    "id": row.id,
                    "namespace": row.namespace,
                    "context_id": row.context_id,
                    "problem_statement": row.problem_statement,
                    "mode": row.mode,
                    "confidence": row.confidence,
                    "service": ContextAgentRepository.row_to_result(row).get("service"),
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ],
        }


@router.get("/context/latest")
async def latest_context_agent_run(namespace: str = "staging") -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextAgentRepository(session)
        row = await repo.latest(namespace)
        if row is None:
            raise HTTPException(status_code=404, detail="No context agent run found")
        return ContextAgentRepository.row_to_result(row)


@router.post("/composer/compose-full")
async def composer_compose_full(body: ComposeFullRequest) -> dict[str, Any]:
    result = await compose_full(
        body.scenario,
        body.namespace,
        environment=body.environment,
        enforce_referee=body.enforce_referee,
        prior_experiment_id=body.prior_experiment_id,
        use_latest_feedback=body.use_latest_feedback,
    )
    return {
        "plan": result["plan"].model_dump(),
        "summary": result["summary"],
        "composer": result["composer"],
        "pre_mortem": result["pre_mortem"],
        "referee": result["referee"],
        "twin_preview": result.get("twin_preview"),
        "prior_feedback": result.get("prior_feedback"),
        "context_agent": result.get("context_agent"),
        "llm_grounded": result.get("llm_grounded", False),
    }


@router.post("/composer/premortem")
async def composer_premortem(body: PremortemRequest) -> dict[str, Any]:
    pre_mortem = await generate_pre_mortem(body.plan, namespace=body.namespace)
    return pre_mortem


@router.post("/red/plan")
async def red_plan(body: RedPlanRequest) -> dict[str, Any]:
    attack = await plan_red_attack(
        round_num=body.round_num,
        namespace=body.namespace,
        include_security=body.include_security,
        security_mix_pct=body.security_mix_pct,
        prior_techniques=body.prior_techniques,
        use_llm=body.use_llm,
    )
    return attack.model_dump(mode="json")


@router.post("/red/execute")
async def red_execute(body: RedExecuteRequest) -> dict[str, Any]:
    return await execute_red_attack(body.attack, body.namespace)


@router.post("/blue/suggest")
async def blue_suggest(body: BlueSuggestRequest) -> list[dict[str, Any]]:
    suggestions = await get_blue_suggestions(body.gaps, use_llm=body.use_llm)
    return [s.model_dump(mode="json") for s in suggestions]


@router.post("/blue/defend")
async def blue_defend(body: BlueDefendRequest) -> dict[str, Any]:
    defense = await defend_red_attack(
        body.attack,
        posture_gaps=body.posture_gaps,
        evidence_summary=body.evidence_summary,
        namespace=body.namespace,
        use_llm=body.use_llm,
    )
    return defense.model_dump(mode="json")


@router.post("/blue/remediate")
async def blue_remediate(defense: BlueDefense) -> dict[str, Any]:
    return await remediate_defense(defense)


@router.post("/blue/verify")
async def blue_verify(body: BlueVerifyRequest) -> dict[str, Any]:
    return await verify_defense(
        body.attack,
        body.defense,
        namespace=body.namespace,
        re_inject=body.re_inject,
    )


@router.post("/referee/validate")
async def referee_validate(body: RefereeValidateRequest) -> dict[str, Any]:
    return await validate_experiment_plan(body.plan, enforce_freeze=body.enforce_freeze)


@router.get("/referee/status")
async def referee_status_route() -> dict[str, Any]:
    return await referee_status()


@router.post("/referee/export-equilibrium")
async def referee_export_equilibrium(body: RefereeExportRequest) -> dict[str, Any]:
    return await export_equilibrium_round(body.campaign_id, body.round_num)


@router.post("/remediator/verify/{experiment_id}/{finding_id}")
async def remediator_verify_finding(experiment_id: str, finding_id: str) -> dict[str, Any]:
    return await verify_finding(experiment_id, finding_id)


@router.get("/remediator/runbook/{experiment_id}/{finding_id}")
async def remediator_runbook(experiment_id: str, finding_id: str) -> dict[str, str]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None or not row.findings_json:
            raise HTTPException(status_code=404, detail="Finding not found")
        import json

        from chaos_agent.remediator.models import RemediationFinding

        payload = json.loads(row.findings_json)
        findings = [RemediationFinding.model_validate(f) for f in payload.get("findings", [])]
        finding = next((f for f in findings if f.id == finding_id), None)
        if finding is None:
            raise HTTPException(status_code=404, detail="Finding not found")
    return {"markdown": render_runbook(finding)}
