"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from chaos_agent.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def init_db() -> None:
    from chaos_agent.storage import orm  # noqa: F401

    import sqlalchemy as sa

    engine = get_engine()

    def _migrate(connection) -> None:
        inspector = sa.inspect(connection)
        if inspector.has_table("experiments"):
            columns = {col["name"] for col in inspector.get_columns("experiments")}
            if "evidence_json" not in columns:
                connection.execute(sa.text("ALTER TABLE experiments ADD COLUMN evidence_json TEXT"))
            if "findings_json" not in columns:
                connection.execute(sa.text("ALTER TABLE experiments ADD COLUMN findings_json TEXT"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
