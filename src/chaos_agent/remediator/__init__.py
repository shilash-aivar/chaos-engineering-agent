"""LLM remediation pipeline — findings, runbooks, tickets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from chaos_agent.remediator.models import RemediationFinding, RemediationResult

if TYPE_CHECKING:
    from chaos_agent.remediator.pipeline import run_remediation_pipeline as _RunRemediationPipeline


async def run_remediation_pipeline(experiment_id: str) -> RemediationResult:
    from chaos_agent.remediator.pipeline import run_remediation_pipeline as _impl

    return await _impl(experiment_id)


__all__ = ["run_remediation_pipeline", "RemediationFinding", "RemediationResult"]
