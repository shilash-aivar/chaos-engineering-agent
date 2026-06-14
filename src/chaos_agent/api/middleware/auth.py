"""Optional API-key auth for mutating routes and WebSockets."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from chaos_agent.config import get_settings

MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
PUBLIC_PATHS = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})


def _extract_api_key(request: Request) -> str | None:
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def verify_api_key(provided: str | None) -> bool:
    settings = get_settings()
    if not settings.api_key:
        return True
    return bool(provided and provided == settings.api_key)


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if not settings.api_key:
            return await call_next(request)

        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        if request.method not in MUTATING_METHODS:
            return await call_next(request)

        provided = _extract_api_key(request)
        if not verify_api_key(provided):
            request_id = getattr(getattr(request.state, "ctx", None), "request_id", None)
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "unauthorized",
                        "message": "Valid API key required for mutating requests",
                        "request_id": request_id,
                    },
                },
            )

        ctx = getattr(request.state, "ctx", None)
        if ctx is not None:
            ctx.authenticated = True
            ctx.auth_method = "api_key"
        return await call_next(request)
