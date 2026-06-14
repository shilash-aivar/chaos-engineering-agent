"""Structured fault-window evidence for LLM agents and UI."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MetricWindowSample(BaseModel):
    name: str
    baseline: Optional[float] = None
    during_peak: Optional[float] = None
    after: Optional[float] = None
    delta_ratio: Optional[float] = None
    unit: str = "ratio"


class LogSummary(BaseModel):
    service: str
    error_count: int = 0
    top_patterns: list[str] = Field(default_factory=list)
    sample_lines: list[str] = Field(default_factory=list)


class TraceSummary(BaseModel):
    path: str
    trace_count: int = 0
    error_spans: int = 0
    p99_ms: Optional[float] = None
    sample_trace_ids: list[str] = Field(default_factory=list)


class FaultWindowEvidence(BaseModel):
    experiment_id: str
    window_start: datetime
    window_end: datetime
    simulated: bool = False
    metrics: list[MetricWindowSample] = Field(default_factory=list)
    logs: list[LogSummary] = Field(default_factory=list)
    traces: list[TraceSummary] = Field(default_factory=list)
    correlations: list[str] = Field(default_factory=list)
    ebpf_metrics: dict[str, Any] = Field(default_factory=dict)


class ObservabilityBackendStatus(BaseModel):
    prometheus: str  # ok | gap
    loki: str
    tempo: str
    detail: dict[str, Optional[str]] = Field(default_factory=dict)
