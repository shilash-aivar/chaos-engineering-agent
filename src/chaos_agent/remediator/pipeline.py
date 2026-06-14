"""Remediation pipeline — evidence → findings → tickets."""

from __future__ import annotations

import json
import logging

from chaos_agent.config import get_settings
from chaos_agent.remediator.analyzer import analyze_evidence_rules
from chaos_agent.remediator.llm import analyze_evidence_llm
from chaos_agent.remediator.models import RemediationResult
from chaos_agent.remediator.writers.github import create_pull_requests, create_tickets
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

logger = logging.getLogger(__name__)


async def run_remediation_pipeline(experiment_id: str) -> RemediationResult:
    settings = get_settings()
    factory = get_session_factory()

    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None or not row.evidence_json:
            return RemediationResult(experiment_id=experiment_id, mode="skipped", summary="No evidence to analyze")

        plan = repo.plan_from_row(row)
        evidence = repo.evidence_from_row(row)
        slo_breached = bool(row.slo_breached)

    mode = "rules"
    summary = "Rule-based remediator analyzed fault-window evidence."
    findings = analyze_evidence_rules(
        experiment_id=experiment_id,
        plan=plan,
        evidence=evidence,
        slo_breached=slo_breached,
    )

    if settings.llm_enabled:
        llm_result = await analyze_evidence_llm(
            experiment_id=experiment_id,
            plan=plan,
            evidence=evidence,
            slo_breached=slo_breached,
        )
        if llm_result is not None:
            findings, summary = llm_result
            mode = "llm"

    if findings:
        findings = await create_tickets(findings)
        findings = await create_pull_requests(findings)

    prs_created = sum(1 for f in findings if f.pr_number)
    result = RemediationResult(
        experiment_id=experiment_id,
        findings=findings,
        summary=summary,
        mode=mode,
        tickets_created=sum(1 for f in findings if f.ticket_number),
    )

    async with factory() as session:
        repo = ExperimentRepository(session)
        await repo.set_findings(experiment_id, result)
        await repo.add_event(
            experiment_id,
            "Remediation pipeline complete",
            f"{len(findings)} findings · mode={mode} · tickets={result.tickets_created} · prs={prs_created}",
        )
        await session.commit()

    logger.info(
        "remediation_complete",
        extra={"experiment_id": experiment_id, "findings": len(findings), "mode": mode},
    )

    if settings.auto_verify_remediation and findings:
        from chaos_agent.remediator.verify import verify_finding

        for finding in findings:
            if finding.status == "open":
                try:
                    await verify_finding(experiment_id, finding.id)
                except Exception as exc:
                    logger.warning("auto_verify_failed", extra={"finding_id": finding.id, "error": str(exc)})

    return result


async def list_remediation_findings(limit: int = 50) -> list[dict]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        rows = await repo.list_with_findings(limit=limit)
        out: list[dict] = []
        for row in rows:
            if not row.findings_json:
                continue
            payload = json.loads(row.findings_json)
            for f in payload.get("findings", []):
                out.append(
                    {
                        "id": f.get("id"),
                        "severity": f.get("severity"),
                        "title": f.get("title"),
                        "prescription": f.get("prescription"),
                        "scope": f.get("scope"),
                        "status": f.get("status", "open"),
                        "experiment_id": f.get("experiment_id") or row.id,
                        "ticket": str(f["ticket_number"]) if f.get("ticket_number") else None,
                        "pr": str(f["pr_number"]) if f.get("pr_number") else None,
                        "source": f.get("source", "rules"),
                    },
                )
        return out
