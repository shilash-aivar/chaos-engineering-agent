"""SAST/DAST scanner result types."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SastFinding(BaseModel):
    scanner: str
    rule_id: str
    severity: str
    message: str
    file_path: str
    cwe: Optional[str] = None
    line: Optional[int] = None
    simulated: bool = False


class DastFinding(BaseModel):
    probe: str
    target_url: str
    severity: str
    message: str
    cwe: Optional[str] = None
    passed: bool = False
    simulated: bool = False


class SastScanResult(BaseModel):
    findings: list[SastFinding] = Field(default_factory=list)
    scanners_used: list[str] = Field(default_factory=list)
    simulated: bool = False


class DastScanResult(BaseModel):
    findings: list[DastFinding] = Field(default_factory=list)
    target_base: str
    simulated: bool = False
