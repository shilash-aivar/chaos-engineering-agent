"""Regression suites from equilibrium Red/Blue rounds and completed experiments."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from chaos_agent.config import get_settings
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.orm import CampaignRow, ExperimentRow
from chaos_agent.storage.repositories.experiments import ExperimentRepository
from chaos_agent.storage.repositories.regression import RegressionRepository


async def list_regression_suites() -> list[dict[str, Any]]:
    factory = get_session_factory()
    suites: list[dict[str, Any]] = []

    async with factory() as session:
        repo = RegressionRepository(session)
        persisted = await repo.list_suites()
        if persisted:
            return [RegressionRepository.to_dict(row) for row in persisted]

        camp_result = await session.execute(select(CampaignRow))
        for camp in camp_result.scalars().all():
            rounds = json.loads(camp.rounds_json or "[]")
            equilibrium = [r for r in rounds if r.get("outcome") == "draw"]
            if equilibrium:
                suites.append(
                    {
                        "id": f"suite-{camp.id}",
                        "name": f"{camp.name} equilibrium",
                        "source": "red_blue",
                        "tests": len(equilibrium),
                        "passing": len(equilibrium),
                        "last_run": camp.last_round_at.isoformat(),
                        "campaign_id": camp.id,
                    },
                )

        exp_result = await session.execute(
            select(ExperimentRow).where(ExperimentRow.state == "complete").limit(20),
        )
        for row in exp_result.scalars().all():
            if row.slo_breached:
                continue
            suites.append(
                {
                    "id": f"suite-{row.id}",
                    "name": row.name,
                    "source": "experiment",
                    "tests": len(json.loads(row.plan_json).get("faults", [])),
                    "passing": len(json.loads(row.plan_json).get("faults", [])),
                    "last_run": (row.completed_at or row.created_at).isoformat(),
                    "experiment_id": row.id,
                },
            )

    if not suites:
        settings = get_settings()
        if settings.demo_mode or settings.seed_data:
            suites.append(
                {
                    "id": "suite-seed",
                    "name": "checkout-pod-kill-baseline",
                    "source": "manual",
                    "tests": 3,
                    "passing": 3,
                    "last_run": "pending first campaign",
                    "demo": True,
                },
            )
    return suites
