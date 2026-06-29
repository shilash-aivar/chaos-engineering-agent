"""Declared context types — Terraform, docs, codebase metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PracticeLevel(str, Enum):
    INFRA = "infra"
    DB = "db"
    DEPENDENCY = "dependency"
    APP = "app"
    SCALING = "scaling"
    SECURITY = "security"
    MONITORING = "monitoring"
    HA = "ha"
    RESILIENCY = "resiliency"
    RELIABILITY = "reliability"


class TerraformResource(BaseModel):
    type: str
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    source_file: str = "main.tf"


class DeclaredDocument(BaseModel):
    name: str
    doc_type: str  # readme, adr, runbook
    claims: list[str] = Field(default_factory=list)
    raw_excerpt: str = ""


class DeclaredContext(BaseModel):
    repo_name: str = "unknown"
    terraform_resources: list[TerraformResource] = Field(default_factory=list)
    documents: list[DeclaredDocument] = Field(default_factory=list)
    code_hints: list[str] = Field(default_factory=list)
    manifest_hints: list[str] = Field(default_factory=list)
    terraform_sources: dict[str, str] = Field(default_factory=dict)
    code_sources: dict[str, str] = Field(default_factory=dict)
    manifest_sources: dict[str, str] = Field(default_factory=dict)


class ContextSnapshot(BaseModel):
    id: str
    repo_name: str
    namespace: str = "staging"
    declared: DeclaredContext
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContextGap(BaseModel):
    id: str
    level: PracticeLevel
    scope: str  # k8s, aws, app, deps, observability
    severity: str
    service: str
    rule: str
    message: str
    declared_evidence: list[str] = Field(default_factory=list)
    observed_evidence: list[str] = Field(default_factory=list)
    policy_rule: Optional[str] = None


class BlueSuggestion(BaseModel):
    finding_id: str
    level: PracticeLevel
    title: str
    action: str
    artifact_type: str  # terraform, code, manifest, config, runbook
    target_path: str
    suggested_diff: str
    requires_approval: bool = True


class ContextAnalysisResult(BaseModel):
    snapshot_id: str
    repo_name: str
    scanned_at: datetime
    declared_summary: dict[str, int]
    gaps: list[ContextGap]
    blue_suggestions: list[BlueSuggestion]
    posture_summary: dict[str, int]
    sast_findings: list[dict[str, Any]] = Field(default_factory=list)
    sast_simulated: bool = False
    understanding: dict[str, Any] = Field(default_factory=dict)
