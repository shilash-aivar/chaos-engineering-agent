"""Remediation API — findings from experiment pipeline."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chaos_agent.remediator.pipeline import list_remediation_findings, run_remediation_pipeline
from chaos_agent.remediator.templates.runbook import render_runbook
from chaos_agent.remediator.verify import verify_finding
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()


class RemediationRunResponse(BaseModel):
    experiment_id: str
    findings_count: int
    mode: str
    summary: str
    tickets_created: int


@router.get("/findings")
async def get_findings() -> list[dict]:
    return await list_remediation_findings()


@router.get("/experiments/{experiment_id}")
async def get_experiment_remediation(experiment_id: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if not row.findings_json:
            return {"experiment_id": experiment_id, "findings": [], "summary": "", "mode": "skipped"}
        import json

        return json.loads(row.findings_json)


@router.post("/experiments/{experiment_id}/run", response_model=RemediationRunResponse)
async def run_remediation(experiment_id: str) -> RemediationRunResponse:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")

    result = await run_remediation_pipeline(experiment_id)
    return RemediationRunResponse(
        experiment_id=result.experiment_id,
        findings_count=len(result.findings),
        mode=result.mode,
        summary=result.summary,
        tickets_created=result.tickets_created,
    )


@router.post("/experiments/{experiment_id}/findings/{finding_id}/verify")
async def verify_remediation_finding(experiment_id: str, finding_id: str) -> dict:
    return await verify_finding(experiment_id, finding_id)


@router.get("/experiments/{experiment_id}/findings/{finding_id}/runbook")
async def get_finding_runbook(experiment_id: str, finding_id: str) -> dict[str, str]:
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
