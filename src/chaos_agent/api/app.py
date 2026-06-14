"""FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chaos_agent.api.middleware import (
    AuditLogMiddleware,
    ApiKeyAuthMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    register_exception_handlers,
)
from chaos_agent.api.routes import (
    agents,
    chaos_dna,
    ci_gate,
    context,
    dashboard,
    experiments,
    health,
    integrations,
    load_tests,
    observability,
    platform,
    plugins,
    policies,
    posture,
    red_blue,
    remediation,
    snapshot,
    ws,
)
from chaos_agent.config import get_settings
from chaos_agent.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Chaos Engineering Agent",
        description="Internal resilience platform — K8s + AWS chaos orchestration",
        version="0.1.0",
        lifespan=lifespan,
    )
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ApiKeyAuthMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(health.router, tags=["health"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
    app.include_router(snapshot.router, prefix="/snapshot", tags=["snapshot"])
    app.include_router(posture.router, prefix="/posture", tags=["posture"])
    app.include_router(context.router, prefix="/context", tags=["context"])
    app.include_router(red_blue.router, prefix="/red-blue", tags=["red-blue"])
    app.include_router(ci_gate.router, prefix="/ci-gate", tags=["ci-gate"])
    app.include_router(observability.router, prefix="/observability", tags=["observability"])
    app.include_router(remediation.router, prefix="/remediation", tags=["remediation"])
    app.include_router(agents.router, prefix="/agents", tags=["agents"])
    app.include_router(policies.router, prefix="/policies", tags=["policies"])
    app.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
    app.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
    app.include_router(chaos_dna.router, prefix="/chaos-dna", tags=["chaos-dna"])
    app.include_router(load_tests.router, prefix="/load-tests", tags=["load-tests"])
    app.include_router(platform.router, prefix="/platform", tags=["platform"])
    app.include_router(ws.router, prefix="/ws", tags=["websocket"])
    return app
