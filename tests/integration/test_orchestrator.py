import pytest

from chaos_agent.config import Settings
from chaos_agent.models import ExperimentSource, FaultExecutor
from chaos_agent.orchestrator.engine import ExperimentEngine
from chaos_agent.storage.database import get_session_factory, init_db
from chaos_agent.storage.repositories.experiments import ExperimentRepository
from chaos_agent.composer.rules import compose_from_scenario


@pytest.fixture
async def db():
    import chaos_agent.storage.database as db_mod

    db_mod._engine = None
    db_mod._session_factory = None

    import chaos_agent.config as cfg

    cfg._settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        simulate_execution=True,
        guard_interval_seconds=1,
        experiment_max_duration_seconds=3,
        baseline_capture_seconds=1,
    )

    await init_db()
    yield
    if db_mod._engine is not None:
        await db_mod._engine.dispose()


@pytest.mark.asyncio
async def test_experiment_lifecycle_simulated(db) -> None:
    plan, _ = asyncio.run(compose_from_scenario("pod kill on checkout", "staging"))
    factory = get_session_factory()

    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.create(plan)
        exp_id = row.id

    engine = ExperimentEngine()
    engine.chaos_mesh.simulate = True
    await engine._run(exp_id)

    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(exp_id)
        assert row is not None
        assert row.state == "complete"
        events = await repo.get_events(exp_id)
        event_names = [e.event for e in events]
        assert "Baseline captured" in event_names
        assert "Fault injected" in event_names
        assert "Rollback complete" in event_names
