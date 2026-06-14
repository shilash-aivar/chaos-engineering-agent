"""Security attack types for Red/Blue adversarial campaigns."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AttackCategory(str, Enum):
    RESILIENCE = "resilience"
    SECURITY = "security"
    HYBRID = "hybrid"


class SecurityAttackSpec(BaseModel):
    id: str
    name: str
    category: AttackCategory
    technique: str
    target_service: str
    description: str
    cwe: Optional[str] = None
    paired_fault: Optional[str] = None
    severity_if_success: str = "high"
    safe_for_staging: bool = True
    framework_id: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    cwe_ids: list[str] = Field(default_factory=list)
    cve_examples: list[str] = Field(default_factory=list)
    mitre_technique_id: Optional[str] = None
    owasp_rank: Optional[str] = None


class CweEntry(BaseModel):
    id: str
    name: str
    example_cves: list[str] = Field(default_factory=list)


class FrameworkCategory(BaseModel):
    id: str
    name: str
    description: str
    cwes: list[CweEntry] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)


class AttackFramework(BaseModel):
    id: str
    name: str
    version: str
    description: str
    source_url: str
    categories: list[FrameworkCategory] = Field(default_factory=list)


class GeneratedAttackPlan(BaseModel):
    framework_id: str
    framework_name: str
    namespace: str
    category_ids: list[str]
    attacks: list[SecurityAttackSpec]
    total_cwes: int
    total_cve_examples: int
    generated_at: str


class RedAttack(BaseModel):
    id: str
    category: AttackCategory
    title: str
    service: str
    technique: str
    description: str
    cwe: Optional[str] = None
    paired_fault: Optional[str] = None
    transcript: str
    faults: list[dict[str, str]] = Field(default_factory=list)


class BlueDefense(BaseModel):
    attack_id: str
    category: AttackCategory
    title: str
    action: str
    artifact_type: str
    target_path: str
    suggested_diff: str
    transcript: str


class RoundResult(BaseModel):
    round: int
    attack: RedAttack
    defense: BlueDefense
    red_points: int
    blue_points: int
    outcome: str
    referee_note: str
    red_transcript: list[str]
    blue_transcript: list[str]


class CampaignSummary(BaseModel):
    id: str
    name: str
    namespace: str
    state: str
    round: int
    max_rounds: int
    red_score: int
    blue_score: int
    leader: str
    include_security: bool
    security_mix_pct: int
    last_round_at: str
    attack_framework_id: Optional[str] = None
    attack_plan_id: Optional[str] = None
    planned_attack_count: int = 0


class CampaignDetail(CampaignSummary):
    rounds: list[RoundResult] = Field(default_factory=list)
    pending_attack: Optional[RedAttack] = None
