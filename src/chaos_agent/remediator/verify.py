"""Verify remediation findings by re-running source experiment."""

from __future__ import annotations

import json
from typing import Any, Optional

from chaos_agent.red_blue.experiments import inject_attack
from chaos_agent.remediator.models import RemediationFinding, RemediationResult
from chaos_agent.security.types import AttackCategory, RedAttack
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository


async def verify_finding(
    experiment_id: str,
    finding_id: str,
) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None or not row.findings_json:
            return {"verified": False, "message": "Experiment or findings not found"}

        payload = json.loads(row.findings_json)
        findings = [RemediationFinding.model_validate(f) for f in payload.get("findings", [])]
        finding = next((f for f in findings if f.id == finding_id), None)
        if finding is None:
            return {"verified": False, "message": "Finding not found"}

        plan = repo.plan_from_row(row)
        attack = RedAttack(
            id=finding_id,
            category=AttackCategory.RESILIENCE,
            title=finding.title,
            service=plan.targets[0].service if plan.targets else "checkout",
            technique=plan.faults[0].type if plan.faults else "pod_kill",
            description=finding.prescription,
            transcript="Remediation verify re-run",
            faults=[{"type": f.type, "target": f.target or plan.targets[0].service} for f in plan.faults],
        )
        result = await inject_attack(attack, plan.blast_radius.namespace)
        verified = result.get("injected") and not result.get("slo_breached")

        for f in findings:
            if f.id == finding_id:
                f.status = "verified" if verified else "open"
                f.verification = (
                    f"Re-run {result.get('experiment_id')}: "
                    f"{'passed' if verified else 'still failing'}"
                )

        updated = RemediationResult(
            experiment_id=experiment_id,
            findings=findings,
            summary=payload.get("summary", ""),
            mode=payload.get("mode", "rules"),
            tickets_created=payload.get("tickets_created", 0),
        )
        await repo.set_findings(experiment_id, updated)
        await repo.add_event(
            experiment_id,
            "Finding verified" if verified else "Verify failed",
            finding_id,
        )
        await session.commit()

    return {
        "verified": verified,
        "finding_id": finding_id,
        "experiment_id": experiment_id,
        "re_run": result,
        "message": "Remediation verified" if verified else "SLO still breaches on re-run",
    }
