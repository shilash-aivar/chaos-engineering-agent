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
