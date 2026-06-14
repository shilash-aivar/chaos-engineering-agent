"""Experiment persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from chaos_agent.models import ExperimentPlan, ExperimentState
from chaos_agent.observability.types import FaultWindowEvidence
from chaos_agent.remediator.models import RemediationResult
from chaos_agent.storage.orm import ExperimentRow, TimelineEventRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, plan: ExperimentPlan) -> ExperimentRow:
        exp_id = f"exp-{uuid.uuid4().hex[:12]}"
        row = ExperimentRow(
            id=exp_id,
            name=plan.name,
            hypothesis=plan.hypothesis,
            state=ExperimentState.PENDING.value,
            source=plan.source.value,
            namespace=plan.blast_radius.namespace,
            environment=plan.blast_radius.environment,
            plan_json=plan.model_dump_json(),
        )
        self.session.add(row)
        await self.add_event(exp_id, "Experiment created", f"Queued in {plan.blast_radius.environment}")
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, experiment_id: str) -> Optional[ExperimentRow]:
        result = await self.session.execute(
            select(ExperimentRow).where(ExperimentRow.id == experiment_id),
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ExperimentRow]:
        result = await self.session.execute(
            select(ExperimentRow).order_by(ExperimentRow.created_at.desc()),
        )
        return list(result.scalars().all())

    async def set_state(
        self,
        experiment_id: str,
        state: ExperimentState,
        *,
        error_message: Optional[str] = None,
    ) -> None:
        values: dict[str, Any] = {
            "state": state.value,
            "updated_at": _utcnow(),
        }
        if error_message is not None:
            values["error_message"] = error_message
        if state in (ExperimentState.COMPLETE, ExperimentState.FAILED):
            values["completed_at"] = _utcnow()
        await self.session.execute(
            update(ExperimentRow).where(ExperimentRow.id == experiment_id).values(**values),
        )
        await self.session.commit()

    async def set_baseline(self, experiment_id: str, baseline: dict[str, float]) -> None:
        await self.session.execute(
            update(ExperimentRow)
            .where(ExperimentRow.id == experiment_id)
            .values(baseline_json=json.dumps(baseline), updated_at=_utcnow()),
        )
        await self.session.commit()

    async def set_findings(self, experiment_id: str, result: RemediationResult) -> None:
        await self.session.execute(
            update(ExperimentRow)
            .where(ExperimentRow.id == experiment_id)
            .values(
                findings_json=result.model_dump_json(),
                findings_count=len(result.findings),
                updated_at=_utcnow(),
            ),
        )
        await self.session.commit()

    async def list_with_findings(self, limit: int = 50) -> list[ExperimentRow]:
        result = await self.session.execute(
            select(ExperimentRow)
            .where(ExperimentRow.findings_json.is_not(None))
            .order_by(ExperimentRow.updated_at.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    @staticmethod
    def evidence_from_row(row: ExperimentRow) -> FaultWindowEvidence:
        if not row.evidence_json:
            raise ValueError("experiment has no evidence")
        return FaultWindowEvidence.model_validate_json(row.evidence_json)

    async def set_evidence(self, experiment_id: str, evidence: FaultWindowEvidence) -> None:
        await self.session.execute(
            update(ExperimentRow)
            .where(ExperimentRow.id == experiment_id)
            .values(evidence_json=evidence.model_dump_json(), updated_at=_utcnow()),
        )
        await self.session.commit()

    async def request_abort(self, experiment_id: str) -> bool:
        row = await self.get(experiment_id)
        if row is None:
            return False
        await self.session.execute(
            update(ExperimentRow)
            .where(ExperimentRow.id == experiment_id)
            .values(abort_requested=True, updated_at=_utcnow()),
        )
        await self.add_event(experiment_id, "Abort requested", "Rollback will be triggered")
        await self.session.commit()
        return True

    async def is_abort_requested(self, experiment_id: str) -> bool:
        row = await self.get(experiment_id)
        return bool(row and row.abort_requested)

    async def mark_slo_breached(self, experiment_id: str) -> None:
        await self.session.execute(
            update(ExperimentRow)
            .where(ExperimentRow.id == experiment_id)
            .values(slo_breached=True, updated_at=_utcnow()),
        )
        await self.session.commit()

    async def add_event(self, experiment_id: str, event: str, detail: Optional[str] = None) -> None:
        self.session.add(
            TimelineEventRow(experiment_id=experiment_id, event=event, detail=detail),
        )

    async def get_events(self, experiment_id: str) -> list[TimelineEventRow]:
        result = await self.session.execute(
            select(TimelineEventRow)
            .where(TimelineEventRow.experiment_id == experiment_id)
            .order_by(TimelineEventRow.created_at.asc()),
        )
        return list(result.scalars().all())

    @staticmethod
    def plan_from_row(row: ExperimentRow) -> ExperimentPlan:
        return ExperimentPlan.model_validate_json(row.plan_json)

    @staticmethod
    def summary_dict(row: ExperimentRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "hypothesis": row.hypothesis,
            "state": row.state,
            "source": row.source,
            "namespace": row.namespace,
            "environment": row.environment,
            "created_at": row.created_at.isoformat(),
            "red_score": row.red_score,
            "blue_score": row.blue_score,
        }

    async def detail_dict(self, row: ExperimentRow) -> dict[str, Any]:
        events = await self.get_events(row.id)
        plan = self.plan_from_row(row)
        evidence = None
        if row.evidence_json:
            evidence = FaultWindowEvidence.model_validate_json(row.evidence_json).model_dump(mode="json")
        findings = None
        if row.findings_json:
            findings = json.loads(row.findings_json)
        baseline = None
        if row.baseline_json:
            baseline = json.loads(row.baseline_json)
        return {
            **self.summary_dict(row),
            "plan": plan.model_dump(),
            "timeline": [
                {
                    "at": e.created_at.isoformat(),
                    "event": e.event,
                    "detail": e.detail,
                }
                for e in events
            ],
            "findings_count": row.findings_count,
            "findings": findings,
            "slo_breached": row.slo_breached,
            "error_message": row.error_message,
            "baseline": baseline,
            "evidence": evidence,
        }
