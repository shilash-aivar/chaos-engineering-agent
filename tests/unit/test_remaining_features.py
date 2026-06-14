"""Tests for demo mode, chaos DNA, and k6 executor."""

from __future__ import annotations

import pytest

from chaos_agent.config import get_settings
from chaos_agent.executors.k6.executor import K6Executor
from chaos_agent.executors.k6.script import build_k6_script
from chaos_agent.models import Fault, FaultExecutor
from chaos_agent.platform.chaos_dna_service import get_chaos_dna
from chaos_agent.platform.regression_service import list_regression_suites
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.orm import CampaignRow
from chaos_agent.storage.repositories.campaign import CampaignRepository
from sqlalchemy import select


@pytest.mark.asyncio
async def test_campaign_seed_skipped_without_demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "seed_data", False)
    factory = get_session_factory()
    async with factory() as session:
        repo = CampaignRepository(session)
        before = len(list((await session.execute(select(CampaignRow))).scalars().all()))
        await repo.seed_if_empty()
        after = len(list((await session.execute(select(CampaignRow))).scalars().all()))
    assert before == after


@pytest.mark.asyncio
async def test_regression_no_seed_without_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "seed_data", False)
    suites = await list_regression_suites()
    assert all(s.get("id") != "suite-seed" for s in suites)


@pytest.mark.asyncio
async def test_chaos_dna_empty_state() -> None:
    data = await get_chaos_dna("nonexistent-ns-xyz")
    assert data["empty_state"] is True
    assert data["profiles"] == []
    assert data["org_score"] == 0


@pytest.mark.asyncio
async def test_k6_executor_simulated() -> None:
    fault = Fault(executor=FaultExecutor.K6, type="load", target="checkout", params={"vus": 10, "duration": "1m"})
    handle = await K6Executor(simulate=True).apply("exp-k6", fault, "staging", 10)
    assert handle.simulated is True


def test_build_k6_script() -> None:
    fault = Fault(executor=FaultExecutor.K6, type="load", target="checkout", params={"vus": 25, "duration": "3m"})
    script = build_k6_script(fault, "staging")
    assert "checkout" in script
    assert "25" in script or "vus" in script.lower()
