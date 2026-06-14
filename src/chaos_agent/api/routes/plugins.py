"""Wasm and eBPF plugin APIs."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from chaos_agent.config import get_settings
from chaos_agent.executors.ebpf.executor import _ACTIVE_HANDLES
from chaos_agent.executors.ebpf.programs import EBPF_FAULT_TYPES
from chaos_agent.plugins.wasm_host import WasmHost

router = APIRouter()
_host = WasmHost()


@router.get("/wasm")
async def list_wasm_plugins() -> dict:
    return {
        "enabled": get_settings().wasm_plugins_enabled,
        "runtime": _host.runtime,
        "plugins": _host.list_plugins(),
    }


class WasmValidateRequest(BaseModel):
    plugin: str
    max_replicas_pct: Optional[int] = None
    gap_count: Optional[int] = None


@router.post("/wasm/validate")
async def validate_wasm_plugin(body: WasmValidateRequest) -> dict:
    if body.plugin == "referee_blast":
        pct = body.max_replicas_pct if body.max_replicas_pct is not None else 0
        result = _host.validate_blast_radius(pct)
    elif body.plugin == "posture_gaps":
        count = body.gap_count if body.gap_count is not None else 0
        result = _host.validate_gap_count(count)
    else:
        return {"passed": False, "message": f"unknown plugin: {body.plugin}", "plugin": body.plugin}
    return result.model_dump()


@router.get("/ebpf/catalog")
async def ebpf_catalog() -> dict[str, Any]:
    settings = get_settings()
    return {
        "enabled": settings.ebpf_enabled,
        "use_tc": settings.ebpf_use_tc,
        "fault_types": EBPF_FAULT_TYPES,
    }


@router.get("/ebpf/status")
async def ebpf_status() -> dict:
    settings = get_settings()
    active = [
        {
            "handle": name,
            "experiment_id": meta.get("experiment_id"),
            "fault_type": meta.get("fault_type"),
            "applied_via": meta.get("applied_via"),
        }
        for name, meta in _ACTIVE_HANDLES.items()
    ]
    return {
        "enabled": settings.ebpf_enabled,
        "use_tc": settings.ebpf_use_tc,
        "simulate": settings.simulate_execution,
        "active_programs": active,
        "active_count": len(active),
        "fault_types_available": len(EBPF_FAULT_TYPES),
    }
