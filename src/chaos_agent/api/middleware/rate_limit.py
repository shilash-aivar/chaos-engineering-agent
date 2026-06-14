"""Rate limiting for expensive API routes."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from chaos_agent.config import get_settings

_LIMITED_PREFIXES = (
    "/experiments",
    "/agents",
    "/load-tests",
    "/red-blue/campaigns",
    "/context/ingest",
)
_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        limit = settings.rate_limit_per_minute
        if limit <= 0:
            return await call_next(request)

        path = request.url.path
        if request.method == "GET" and not path.startswith("/ws"):
            return await call_next(request)
        if not any(path.startswith(prefix) for prefix in _LIMITED_PREFIXES):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        bucket_key = f"{client}:{api_key}"
        now = time.monotonic()
        window = _BUCKETS[bucket_key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit:
            request_id = getattr(getattr(request.state, "ctx", None), "request_id", None)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "request_id": request_id,
                },
            )
        window.append(now)
        return await call_next(request)
