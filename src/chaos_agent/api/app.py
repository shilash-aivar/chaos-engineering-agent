"""FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chaos_agent.api.routes import dashboard, experiments, health, posture, red_blue, snapshot
from chaos_agent.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chaos Engineering Agent",
        description="Internal resilience platform — K8s + AWS chaos orchestration",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
    app.include_router(snapshot.router, prefix="/snapshot", tags=["snapshot"])
    app.include_router(posture.router, prefix="/posture", tags=["posture"])
    app.include_router(red_blue.router, prefix="/red-blue", tags=["red-blue"])
    return app
