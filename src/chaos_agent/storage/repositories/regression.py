"""Regression suite persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chaos_agent.storage.orm import RegressionSuiteRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RegressionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_suite(
        self,
        *,
        name: str,
        source: str,
        payload: dict[str, Any],
        campaign_id: Optional[str] = None,
        round_num: Optional[int] = None,
        experiment_id: Optional[str] = None,
        tests: int = 1,
        passing: int = 1,
    ) -> RegressionSuiteRow:
        suite_id = f"suite-{uuid.uuid4().hex[:10]}"
        row = RegressionSuiteRow(
            id=suite_id,
            name=name,
            source=source,
            campaign_id=campaign_id,
            round_num=round_num,
            experiment_id=experiment_id,
            payload_json=json.dumps(payload),
            tests=tests,
            passing=passing,
            last_run=_utcnow(),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_suites(self, limit: int = 50) -> list[RegressionSuiteRow]:
        result = await self.session.execute(
            select(RegressionSuiteRow).order_by(RegressionSuiteRow.created_at.desc()).limit(limit),
        )
        return list(result.scalars().all())

    async def get_suite(self, suite_id: str) -> Optional[RegressionSuiteRow]:
        result = await self.session.execute(
            select(RegressionSuiteRow).where(RegressionSuiteRow.id == suite_id),
        )
        return result.scalar_one_or_none()

    @staticmethod
    def to_dict(row: RegressionSuiteRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "source": row.source,
            "tests": row.tests,
            "passing": row.passing,
            "last_run": row.last_run.isoformat() if row.last_run else None,
            "campaign_id": row.campaign_id,
            "round_num": row.round_num,
            "experiment_id": row.experiment_id,
            "payload": json.loads(row.payload_json),
        }
