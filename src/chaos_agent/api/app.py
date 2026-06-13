"""FastAPI application."""

from fastapi import FastAPI

from chaos_agent.api.routes import experiments, health, posture, red_blue


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chaos Engineering Agent",
        description="Internal resilience platform — K8s + AWS chaos orchestration",
        version="0.1.0",
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
    app.include_router(posture.router, prefix="/posture", tags=["posture"])
    app.include_router(red_blue.router, prefix="/red-blue", tags=["red-blue"])
    return app
