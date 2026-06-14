"""CI gate API — PR-scoped security probes + chaos fault."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from chaos_agent.ci_gate.evaluator import evaluate_pr

router = APIRouter()


class CiGateRequest(BaseModel):
    pr_number: int
    changed_files: list[str] = Field(default_factory=list)
    changed_services: list[str] = Field(default_factory=list)
    namespace: str = "staging"


@router.post("/evaluate")
async def evaluate_ci_gate(body: CiGateRequest) -> dict:
    return await evaluate_pr(
        pr_number=body.pr_number,
        changed_files=body.changed_files,
        changed_services=body.changed_services,
        namespace=body.namespace,
    )
