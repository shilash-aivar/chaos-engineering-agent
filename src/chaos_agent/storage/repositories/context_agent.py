"""Persistence for context-agent understanding runs."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chaos_agent.storage.orm import ContextAgentRunRow


class ContextAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_run(
        self,
        result: dict[str, Any],
        *,
        context_id: Optional[str] = None,
    ) -> ContextAgentRunRow:
        row = ContextAgentRunRow(
            id=f"ctx-agent-{uuid.uuid4().hex[:12]}",
            namespace=str(result.get("namespace") or "staging"),
            context_id=context_id,
            problem_statement=str(result.get("problem_statement") or ""),
            mode=str(result.get("mode") or "rules"),
            confidence=str(result.get("confidence") or "low"),
            result_json=json.dumps(result, default=str),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def latest(self, namespace: str = "staging") -> Optional[ContextAgentRunRow]:
        result = await self.session.execute(
            select(ContextAgentRunRow)
            .where(ContextAgentRunRow.namespace == namespace)
            .order_by(ContextAgentRunRow.created_at.desc())
            .limit(1),
        )
        return result.scalar_one_or_none()

    async def list_runs(self, namespace: str = "staging", limit: int = 20) -> list[ContextAgentRunRow]:
        result = await self.session.execute(
            select(ContextAgentRunRow)
            .where(ContextAgentRunRow.namespace == namespace)
            .order_by(ContextAgentRunRow.created_at.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    @staticmethod
    def row_to_result(row: ContextAgentRunRow) -> dict[str, Any]:
        payload = json.loads(row.result_json)
        payload.setdefault("id", row.id)
        payload.setdefault("created_at", row.created_at.isoformat())
        return payload

