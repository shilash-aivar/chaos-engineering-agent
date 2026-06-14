"""Structured request audit logging."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("chaos_agent.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        ctx = getattr(request.state, "ctx", None)
        logger.info(
            "http_request",
            extra={
                "request_id": ctx.request_id if ctx else None,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": elapsed_ms,
                "authenticated": ctx.authenticated if ctx else False,
            },
        )
        return response
