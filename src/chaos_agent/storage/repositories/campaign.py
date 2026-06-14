"""Campaign and attack plan persistence."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chaos_agent.security.types import CampaignDetail, CampaignSummary, GeneratedAttackPlan, RoundResult
from chaos_agent.storage.orm import AttackPlanRow, CampaignRow, RemediationRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CampaignRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def seed_if_empty(self) -> None:
        result = await self.session.execute(select(CampaignRow).limit(1))
        if result.scalar_one_or_none() is not None:
            return
        now = _utcnow()
        for camp_id, name, rnd, red, blue, leader, state, sec in [
            ("camp-001", "checkout-game-day", 2, 61, 54, "red", "active", False),
            ("camp-002", "payments-hardening", 3, 48, 72, "blue", "complete", True),
        ]:
            self.session.add(
                CampaignRow(
                    id=camp_id,
                    name=name,
                    namespace="staging",
                    state=state,
                    round=rnd,
                    max_rounds=3,
                    red_score=red,
                    blue_score=blue,
                    leader=leader,
                    include_security=sec,
                    security_mix_pct=60 if sec else 0,
                    planned_attack_count=0,
                    rounds_json="[]",
                    last_round_at=now,
                    created_at=now,
                ),
            )
        await self.session.commit()

    async def list_campaigns(self) -> list[CampaignSummary]:
        await self.seed_if_empty()
        result = await self.session.execute(
            select(CampaignRow).order_by(CampaignRow.last_round_at.desc()),
        )
        return [self._row_summary(r) for r in result.scalars().all()]

    async def get_campaign(self, campaign_id: str) -> Optional[CampaignDetail]:
        row = await self._get_row(campaign_id)
        if row is None:
            return None
        rounds = [RoundResult.model_validate(r) for r in json.loads(row.rounds_json or "[]")]
        return CampaignDetail(**self._row_summary(row).model_dump(), rounds=rounds)

    async def save_campaign(self, camp: dict[str, Any]) -> CampaignRow:
        row = CampaignRow(
            id=camp["id"],
            name=camp["name"],
            namespace=camp["namespace"],
            state=camp["state"],
            round=camp["round"],
            max_rounds=camp["max_rounds"],
            red_score=camp["red_score"],
            blue_score=camp["blue_score"],
            leader=camp["leader"],
            include_security=camp["include_security"],
            security_mix_pct=camp["security_mix_pct"],
            attack_framework_id=camp.get("attack_framework_id"),
            attack_plan_id=camp.get("attack_plan_id"),
            planned_attack_count=camp.get("planned_attack_count", 0),
            rounds_json=json.dumps(camp.get("rounds", [])),
            last_round_at=datetime.fromisoformat(camp["last_round_at"].replace("Z", "+00:00"))
            if isinstance(camp["last_round_at"], str)
            else camp["last_round_at"],
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def update_campaign(self, camp: dict[str, Any]) -> None:
        row = await self._get_row(camp["id"])
        if row is None:
            return
        row.state = camp["state"]
        row.round = camp["round"]
        row.red_score = camp["red_score"]
        row.blue_score = camp["blue_score"]
        row.leader = camp["leader"]
        row.rounds_json = json.dumps(camp.get("rounds", []))
        row.last_round_at = datetime.fromisoformat(camp["last_round_at"].replace("Z", "+00:00"))
        await self.session.commit()

    async def save_attack_plan(self, plan: GeneratedAttackPlan, plan_id: Optional[str] = None) -> str:
        pid = plan_id or f"plan-{uuid.uuid4().hex[:8]}"
        existing = await self.session.get(AttackPlanRow, pid)
        if existing:
            return pid
        self.session.add(
            AttackPlanRow(
                id=pid,
                framework_id=plan.framework_id,
                plan_json=plan.model_dump_json(),
            ),
        )
        await self.session.commit()
        return pid

    async def get_attack_plan(self, plan_id: str) -> Optional[GeneratedAttackPlan]:
        row = await self.session.get(AttackPlanRow, plan_id)
        if row is None:
            return None
        return GeneratedAttackPlan.model_validate_json(row.plan_json)

    async def save_remediation(
        self,
        *,
        campaign_id: str,
        round_num: int,
        defense_json: str,
        pr_url: Optional[str] = None,
        pr_number: Optional[int] = None,
        status: str = "pr_opened",
    ) -> RemediationRow:
        rem_id = f"rem-{uuid.uuid4().hex[:8]}"
        row = RemediationRow(
            id=rem_id,
            campaign_id=campaign_id,
            round_num=round_num,
            defense_json=defense_json,
            pr_url=pr_url,
            pr_number=pr_number,
            status=status,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get_remediation(self, campaign_id: str, round_num: int) -> Optional[RemediationRow]:
        result = await self.session.execute(
            select(RemediationRow)
            .where(RemediationRow.campaign_id == campaign_id)
            .where(RemediationRow.round_num == round_num),
        )
        return result.scalar_one_or_none()

    async def mark_verified(self, rem_id: str) -> None:
        row = await self.session.get(RemediationRow, rem_id)
        if row:
            row.verified = True
            row.status = "verified"
            await self.session.commit()

    async def _get_row(self, campaign_id: str) -> Optional[CampaignRow]:
        return await self.session.get(CampaignRow, campaign_id)

    @staticmethod
    def _row_summary(row: CampaignRow) -> CampaignSummary:
        return CampaignSummary(
            id=row.id,
            name=row.name,
            namespace=row.namespace,
            state=row.state,
            round=row.round,
            max_rounds=row.max_rounds,
            red_score=row.red_score,
            blue_score=row.blue_score,
            leader=row.leader,
            include_security=row.include_security,
            security_mix_pct=row.security_mix_pct,
            last_round_at=row.last_round_at.isoformat(),
            attack_framework_id=row.attack_framework_id,
            attack_plan_id=row.attack_plan_id,
            planned_attack_count=row.planned_attack_count,
        )
