"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from chaos_agent.storage.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentRow(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    hypothesis: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(32))
    namespace: Mapped[str] = mapped_column(String(128))
    environment: Mapped[str] = mapped_column(String(32))
    plan_json: Mapped[str] = mapped_column(Text)
    baseline_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    abort_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    slo_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    red_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blue_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class TimelineEventRow(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(String(64), index=True)
    event: Mapped[str] = mapped_column(String(128))
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContextSnapshotRow(Base):
    __tablename__ = "context_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    repo_name: Mapped[str] = mapped_column(String(256))
    namespace: Mapped[str] = mapped_column(String(128))
    declared_json: Mapped[str] = mapped_column(Text)
    analysis_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContextAgentRunRow(Base):
    __tablename__ = "context_agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    namespace: Mapped[str] = mapped_column(String(128), index=True)
    context_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    problem_statement: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[str] = mapped_column(String(32))
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AttackPlanRow(Base):
    __tablename__ = "attack_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    framework_id: Mapped[str] = mapped_column(String(64))
    plan_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CampaignRow(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    namespace: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(32))
    round: Mapped[int] = mapped_column(Integer, default=0)
    max_rounds: Mapped[int] = mapped_column(Integer, default=3)
    red_score: Mapped[int] = mapped_column(Integer, default=0)
    blue_score: Mapped[int] = mapped_column(Integer, default=0)
    leader: Mapped[str] = mapped_column(String(16), default="draw")
    include_security: Mapped[bool] = mapped_column(Boolean, default=False)
    security_mix_pct: Mapped[int] = mapped_column(Integer, default=0)
    attack_framework_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    attack_plan_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    planned_attack_count: Mapped[int] = mapped_column(Integer, default=0)
    rounds_json: Mapped[str] = mapped_column(Text, default="[]")
    last_round_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RegressionSuiteRow(Base):
    __tablename__ = "regression_suites"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    source: Mapped[str] = mapped_column(String(32))
    campaign_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    round_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experiment_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text)
    tests: Mapped[int] = mapped_column(Integer, default=1)
    passing: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class RemediationRow(Base):
    __tablename__ = "remediations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(64), index=True)
    round_num: Mapped[int] = mapped_column(Integer)
    defense_json: Mapped[str] = mapped_column(Text)
    pr_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    pr_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
