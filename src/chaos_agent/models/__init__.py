"""Pydantic domain models — mirror schemas/*.json."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExperimentState(StrEnum):
    PENDING = "pending"
    SIMULATING = "simulating"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    ABORTING = "aborting"
    COMPLETE = "complete"
    FAILED = "failed"


class ExperimentSource(StrEnum):
    HUMAN = "human"
    LLM = "llm"
    RED_AGENT = "red_agent"
    CI = "ci"
    HYBRID = "hybrid"


class FaultExecutor(StrEnum):
    CHAOS_MESH = "chaos_mesh"
    AWS_FIS = "aws_fis"
    TOXIPROXY = "toxiproxy"
    K6 = "k6"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Target(BaseModel):
    service: str
    namespace: str


class Fault(BaseModel):
    executor: FaultExecutor
    type: str
    target: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class BlastRadius(BaseModel):
    max_replicas_pct: float = 30.0
    namespace: str
    environment: str = "staging"


class RollbackSpec(BaseModel):
    type: str
    ttl_seconds: int = 300


class ExperimentPlan(BaseModel):
    name: str
    hypothesis: str
    targets: list[Target]
    faults: list[Fault]
    blast_radius: BlastRadius
    watch_metrics: list[str]
    rollback: RollbackSpec
    source: ExperimentSource = ExperimentSource.HUMAN
    infra_evidence: list[str] = Field(default_factory=list)
    load: dict[str, Any] | None = None


class Prescription(BaseModel):
    scope: str
    action: str
    type: str | None = None
    target: str | None = None
    terraform_path: str | None = None
    manifest_path: str | None = None


class Finding(BaseModel):
    id: str
    severity: Severity
    evidence: list[str]
    prescription: Prescription
    verification: str | None = None


class RoundScore(BaseModel):
    round_id: str
    experiment_id: str
    red_score: float = Field(ge=0, le=100)
    blue_score: float = Field(ge=0, le=100)
    winner: str | None = None
    slo_breached: bool = False
    recovery_seconds: float | None = None


class ExperimentRecord(BaseModel):
    id: str
    plan: ExperimentPlan
    state: ExperimentState = ExperimentState.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    snapshot_id: str | None = None
