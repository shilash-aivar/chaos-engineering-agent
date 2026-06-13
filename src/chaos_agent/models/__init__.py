"""Pydantic domain models — mirror schemas/*.json."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExperimentState(str, Enum):
    PENDING = "pending"
    SIMULATING = "simulating"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    ABORTING = "aborting"
    COMPLETE = "complete"
    FAILED = "failed"


class ExperimentSource(str, Enum):
    HUMAN = "human"
    LLM = "llm"
    RED_AGENT = "red_agent"
    CI = "ci"
    HYBRID = "hybrid"


class FaultExecutor(str, Enum):
    CHAOS_MESH = "chaos_mesh"
    AWS_FIS = "aws_fis"
    TOXIPROXY = "toxiproxy"
    K6 = "k6"


class Severity(str, Enum):
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
    target: Optional[str] = None
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
    load: Optional[dict[str, Any]] = None


class Prescription(BaseModel):
    scope: str
    action: str
    type: Optional[str] = None
    target: Optional[str] = None
    terraform_path: Optional[str] = None
    manifest_path: Optional[str] = None


class Finding(BaseModel):
    id: str
    severity: Severity
    evidence: list[str]
    prescription: Prescription
    verification: Optional[str] = None


class RoundScore(BaseModel):
    round_id: str
    experiment_id: str
    red_score: float = Field(ge=0, le=100)
    blue_score: float = Field(ge=0, le=100)
    winner: Optional[str] = None
    slo_breached: bool = False
    recovery_seconds: Optional[float] = None


class ExperimentRecord(BaseModel):
    id: str
    plan: ExperimentPlan
    state: ExperimentState = ExperimentState.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    snapshot_id: Optional[str] = None
