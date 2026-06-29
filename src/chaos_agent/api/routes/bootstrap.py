"""Bootstrap detector API — read-only install gap status."""

from __future__ import annotations

from fastapi import APIRouter

from chaos_agent.bootstrap.service import detect_bootstrap_status
from chaos_agent.platform.target_context_service import get_context_by_id

router = APIRouter()


@router.get("/status")
async def bootstrap_status(namespace: str = "staging", context_id: str | None = None) -> dict:
    cluster = None
    if context_id:
        ctx = get_context_by_id(context_id)
        if ctx:
            namespace = ctx.get("namespace", namespace)
            cluster = ctx.get("kube_context") or ctx.get("cluster")
    return await detect_bootstrap_status(namespace, cluster=cluster)
