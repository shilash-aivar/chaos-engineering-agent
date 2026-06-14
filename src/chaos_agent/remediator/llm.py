"""LLM-powered remediation analysis."""

from __future__ import annotations

import json
import uuid
from typing import Optional

from chaos_agent.composer.prompts import REMEDIATOR_SYSTEM
from chaos_agent.llm.client import get_llm_client
from chaos_agent.models import ExperimentPlan, Severity
from chaos_agent.observability.types import FaultWindowEvidence
from chaos_agent.remediator.models import RemediationFinding


async def analyze_evidence_llm(
    *,
    experiment_id: str,
    plan: ExperimentPlan,
    evidence: FaultWindowEvidence,
    slo_breached: bool,
) -> Optional[tuple[list[RemediationFinding], str]]:
    llm = get_llm_client()
    if not llm.available:
        return None

    payload = {
        "experiment_id": experiment_id,
        "hypothesis": plan.hypothesis,
        "faults": [f.model_dump() for f in plan.faults],
        "watch_metrics": plan.watch_metrics,
        "slo_breached": slo_breached,
        "evidence": evidence.model_dump(mode="json"),
        "infra_evidence": plan.infra_evidence,
    }

    data = await llm.complete_json(system=REMEDIATOR_SYSTEM, user=json.dumps(payload, indent=2))
    if not data or "findings" not in data:
        return None

    findings: list[RemediationFinding] = []
    for raw in data.get("findings", [])[:8]:
        try:
            findings.append(
                RemediationFinding(
                    id=str(raw.get("id") or f"find-{uuid.uuid4().hex[:8]}"),
                    severity=Severity(str(raw.get("severity", "medium"))),
                    title=str(raw.get("title", "Remediation finding")),
                    scope=raw.get("scope", "app"),
                    evidence=list(raw.get("evidence") or ["LLM diagnosis"]),
                    prescription=str(raw.get("prescription", "Review and apply fix")),
                    target_path=str(raw.get("target_path", "")),
                    artifact_type=str(raw.get("artifact_type", "runbook")),
                    suggested_diff=str(raw.get("suggested_diff", "")),
                    verification=raw.get("verification"),
                    experiment_id=experiment_id,
                    source="llm",
                ),
            )
        except Exception:
            continue

    if not findings:
        return None
    return findings, str(data.get("summary") or "LLM remediator analyzed fault-window evidence.")
