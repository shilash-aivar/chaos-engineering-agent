"""Remediation finding types for the agent pipeline."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from chaos_agent.models import Severity


class RemediationFinding(BaseModel):
    id: str
    severity: Severity
    title: str
    scope: Literal["k8s", "aws", "mesh", "app", "observability"]
    evidence: list[str] = Field(min_length=1)
    prescription: str
    target_path: str = ""
    artifact_type: str = "runbook"
    suggested_diff: str = ""
    verification: Optional[str] = None
    ticket_url: Optional[str] = None
    ticket_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    status: Literal["open", "in_progress", "verified", "closed"] = "open"
    experiment_id: Optional[str] = None
    source: Literal["llm", "rules"] = "rules"


class RemediationResult(BaseModel):
    experiment_id: str
    findings: list[RemediationFinding] = Field(default_factory=list)
    summary: str = ""
    mode: Literal["llm", "rules", "skipped"] = "rules"
    tickets_created: int = 0
