"""Experiment orchestration — state machine, guard, rollback."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from chaos_agent.collectors.prometheus.client import PrometheusClient
from chaos_agent.composer.validators.safety import SafetyValidationError, validate_plan
from chaos_agent.config import get_settings
from chaos_agent.executors.base import RollbackHandle
from chaos_agent.executors.chaos_mesh.executor import ChaosMeshExecutor
from chaos_agent.executors.toxiproxy.executor import ToxiproxyExecutor
from chaos_agent.models import ExperimentPlan, ExperimentState, FaultExecutor
from chaos_agent.orchestrator.guards.steady_state import SteadyStateGuard
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

if TYPE_CHECKING:
    from chaos_agent.storage.orm import ExperimentRow

logger = logging.getLogger(__name__)


class ExperimentEngine:
    """Runs experiments asynchronously with guard + rollback."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.prom = PrometheusClient()
        self.guard = SteadyStateGuard(self.prom)
        self.chaos_mesh = ChaosMeshExecutor()
        self.toxiproxy = ToxiproxyExecutor()
        self._running: dict[str, asyncio.Task[None]] = {}

    async def start(self, experiment_id: str) -> None:
        if experiment_id in self._running:
            return
        task = asyncio.create_task(self._run(experiment_id))
        self._running[experiment_id] = task
        task.add_done_callback(lambda _: self._running.pop(experiment_id, None))

    async def _repo(self) -> ExperimentRepository:
        factory = get_session_factory()
        session = factory()
        return ExperimentRepository(session)

    async def _run(self, experiment_id: str) -> None:
        factory = get_session_factory()
        async with factory() as session:
            repo = ExperimentRepository(session)
            row = await repo.get(experiment_id)
            if row is None:
                return

            plan = repo.plan_from_row(row)
            handles: list[RollbackHandle] = []

            if await repo.is_abort_requested(experiment_id):
                await repo.set_state(experiment_id, ExperimentState.COMPLETE)
                await repo.add_event(experiment_id, "Aborted before start")
                await session.commit()
                return

            try:
                validate_plan(plan)
            except SafetyValidationError as exc:
                await repo.set_state(experiment_id, ExperimentState.FAILED, error_message=str(exc))
                await repo.add_event(experiment_id, "Safety validation failed", str(exc))
                await session.commit()
                return

            simulate = self.settings.simulate_execution
            if not simulate:
                prom_ok = await self.prom.is_available()
                chaos_ok = await self.chaos_mesh.is_available()
                if not prom_ok or not chaos_ok:
                    simulate = True
                    await repo.add_event(
                        experiment_id,
                        "Simulation mode",
                        "Prometheus or Kubernetes unavailable — simulating fault lifecycle",
                    )
                    await session.commit()
                    self.chaos_mesh.simulate = True

            try:
                await repo.set_state(experiment_id, ExperimentState.RUNNING)
                await repo.add_event(experiment_id, "Capturing baseline", "Prometheus steady-state window")
                await session.commit()

                baseline = await self.guard.capture_baseline(plan.watch_metrics)
                if not baseline:
                    baseline = {m: 0.0 for m in plan.watch_metrics}
                await repo.set_baseline(experiment_id, baseline)
                await repo.add_event(
                    experiment_id,
                    "Baseline captured",
                    ", ".join(f"{k}={v:.4f}" for k, v in baseline.items()),
                )
                await session.commit()

                for fault in plan.faults:
                    if fault.executor == FaultExecutor.CHAOS_MESH:
                        handle = await self.chaos_mesh.apply(
                            experiment_id,
                            fault,
                            plan.blast_radius.namespace,
                            plan.blast_radius.max_replicas_pct,
                        )
                        handles.append(handle)
                        await repo.add_event(
                            experiment_id,
                            "Fault injected",
                            f"chaos_mesh/{fault.type} → {fault.target}",
                        )
                        await session.commit()
                    elif fault.executor == FaultExecutor.TOXIPROXY:
                        handle = await self.toxiproxy.apply(
                            experiment_id,
                            fault,
                            plan.blast_radius.namespace,
                            plan.blast_radius.max_replicas_pct,
                        )
                        handles.append(handle)
                        await repo.add_event(
                            experiment_id,
                            "Fault injected",
                            f"toxiproxy/{fault.type} → {fault.target}",
                        )
                        await session.commit()

                await self._monitor_loop(repo, session, experiment_id, plan, baseline, handles)

            except Exception as exc:
                logger.exception("experiment_failed", extra={"experiment_id": experiment_id})
                await repo.set_state(experiment_id, ExperimentState.FAILED, error_message=str(exc))
                await repo.add_event(experiment_id, "Experiment failed", str(exc))
                await session.commit()
                await self._rollback_all(handles)

    async def _monitor_loop(
        self,
        repo: ExperimentRepository,
        session,
        experiment_id: str,
        plan: ExperimentPlan,
        baseline: dict[str, float],
        handles: list[RollbackHandle],
    ) -> None:
        elapsed = 0
        aborted = False
        breach_reason: Optional[str] = None
        max_duration = self.settings.experiment_max_duration_seconds
        if self.chaos_mesh.simulate:
            max_duration = min(max_duration, 45)

        while elapsed < max_duration:
            if await repo.is_abort_requested(experiment_id):
                aborted = True
                breach_reason = "manual abort"
                break

            current = await self.prom.snapshot(plan.watch_metrics)
            if not current and self.chaos_mesh.simulate:
                await asyncio.sleep(self.settings.guard_interval_seconds)
                elapsed += self.settings.guard_interval_seconds
                continue

            breach = self.guard.check(baseline, current)
            if breach.breached:
                aborted = True
                breach_reason = (
                    f"{breach.metric}: {breach.current:.4f} vs baseline {breach.baseline:.4f} "
                    f"({breach.reason})"
                )
                await repo.mark_slo_breached(experiment_id)
                await repo.add_event(experiment_id, "SLO breach detected", breach_reason)
                await session.commit()
                break

            await asyncio.sleep(self.settings.guard_interval_seconds)
            elapsed += self.settings.guard_interval_seconds

        await repo.set_state(experiment_id, ExperimentState.ABORTING)
        await repo.add_event(
            experiment_id,
            "Rollback started",
            breach_reason or "duration complete",
        )
        await session.commit()

        await self._rollback_all(handles)
        await repo.add_event(experiment_id, "Rollback complete", "Fault resources removed")
        await session.commit()

        recovered = await self.guard.wait_for_recovery(baseline, plan.watch_metrics)
        await repo.add_event(
            experiment_id,
            "Recovery check",
            "metrics at baseline" if recovered else "metrics still degraded",
        )
        await repo.set_state(experiment_id, ExperimentState.COMPLETE)
        await session.commit()

    async def _rollback_all(self, handles: list[RollbackHandle]) -> None:
        for handle in handles:
            try:
                if handle.executor == "toxiproxy":
                    await self.toxiproxy.rollback(handle)
                else:
                    await self.chaos_mesh.rollback(handle)
            except Exception as exc:
                logger.warning("rollback_failed", extra={"error": str(exc)})

        if handles:
            ttl = self.settings.rollback_ttl_seconds
            asyncio.create_task(self._ttl_safety_net(handles, ttl))

    async def _ttl_safety_net(self, handles: list[RollbackHandle], ttl_seconds: int) -> None:
        await asyncio.sleep(ttl_seconds)
        for handle in handles:
            try:
                if handle.executor == "toxiproxy":
                    await self.toxiproxy.rollback(handle)
                else:
                    await self.chaos_mesh.rollback(handle)
            except Exception as exc:
                logger.warning("ttl_rollback_failed", extra={"error": str(exc)})

    async def request_abort(self, experiment_id: str) -> bool:
        factory = get_session_factory()
        async with factory() as session:
            repo = ExperimentRepository(session)
            row = await repo.get(experiment_id)
            if row is None:
                return False
            if row.state not in (
                ExperimentState.RUNNING.value,
                ExperimentState.AWAITING_APPROVAL.value,
                ExperimentState.PENDING.value,
            ):
                return False
            return await repo.request_abort(experiment_id)


_engine: Optional[ExperimentEngine] = None


def get_engine() -> ExperimentEngine:
    global _engine
    if _engine is None:
        _engine = ExperimentEngine()
    return _engine
