"""Context snapshot persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chaos_agent.blue.agent import suggest_fixes
from chaos_agent.context.analyzer import analyze_context, sast_findings_to_gaps
from chaos_agent.context.types import ContextAnalysisResult, ContextSnapshot, DeclaredContext
from chaos_agent.context.understanding import understanding_from_snapshot
from chaos_agent.platform.target_context_service import snapshot_builder_for_namespace
from chaos_agent.security.scanners.sast import run_sast_scan
from chaos_agent.storage.orm import ContextSnapshotRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_ingest(
        self,
        snapshot: ContextSnapshot,
    ) -> ContextSnapshotRow:
        row = ContextSnapshotRow(
            id=snapshot.id,
            repo_name=snapshot.repo_name,
            namespace=snapshot.namespace,
            declared_json=snapshot.declared.model_dump_json(),
            ingested_at=snapshot.ingested_at,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get_latest(self, namespace: str = "staging") -> Optional[ContextSnapshotRow]:
        result = await self.session.execute(
            select(ContextSnapshotRow)
            .where(ContextSnapshotRow.namespace == namespace)
            .order_by(ContextSnapshotRow.ingested_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, snapshot_id: str) -> Optional[ContextSnapshotRow]:
        result = await self.session.execute(
            select(ContextSnapshotRow).where(ContextSnapshotRow.id == snapshot_id),
        )
        return result.scalar_one_or_none()

    async def list_snapshots(self, namespace: str = "staging", limit: int = 20) -> list[ContextSnapshotRow]:
        result = await self.session.execute(
            select(ContextSnapshotRow)
            .where(ContextSnapshotRow.namespace == namespace)
            .order_by(ContextSnapshotRow.ingested_at.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    async def delete(self, snapshot_id: str) -> bool:
        row = await self.get_by_id(snapshot_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True

    async def run_analysis(self, row: ContextSnapshotRow) -> ContextAnalysisResult:
        declared = DeclaredContext.model_validate_json(row.declared_json)
        snapshot = ContextSnapshot(
            id=row.id,
            repo_name=row.repo_name,
            namespace=row.namespace,
            declared=declared,
            ingested_at=row.ingested_at,
        )
        gaps, posture_summary = await analyze_context(snapshot, row.namespace)

        sast = run_sast_scan(
            terraform_files=declared.terraform_sources,
            code_files=declared.code_sources,
        )
        sast_dicts = [f.model_dump() for f in sast.findings]
        if sast_dicts:
            gaps.extend(sast_findings_to_gaps(sast_dicts, len(gaps)))

        blue = suggest_fixes(gaps)

        declared_summary = {
            "terraform_resources": len(declared.terraform_resources),
            "documents": len(declared.documents),
            "code_hints": len(declared.code_hints),
            "manifest_hints": len(declared.manifest_hints),
        }

        infra = await snapshot_builder_for_namespace(row.namespace).build()
        understanding = understanding_from_snapshot(snapshot, infra)

        result = ContextAnalysisResult(
            snapshot_id=row.id,
            repo_name=row.repo_name,
            scanned_at=_utcnow(),
            declared_summary=declared_summary,
            gaps=gaps,
            blue_suggestions=blue,
            posture_summary=posture_summary,
            sast_findings=sast_dicts,
            sast_simulated=sast.simulated,
            understanding=understanding,
        )

        row.analysis_json = result.model_dump_json()
        await self.session.commit()
        return result

    @staticmethod
    def row_to_snapshot(row: ContextSnapshotRow) -> ContextSnapshot:
        return ContextSnapshot(
            id=row.id,
            repo_name=row.repo_name,
            namespace=row.namespace,
            declared=DeclaredContext.model_validate_json(row.declared_json),
            ingested_at=row.ingested_at,
        )

    @staticmethod
    def analysis_from_row(row: ContextSnapshotRow) -> Optional[ContextAnalysisResult]:
        if not row.analysis_json:
            return None
        return ContextAnalysisResult.model_validate_json(row.analysis_json)
