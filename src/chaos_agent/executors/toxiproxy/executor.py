"""Toxiproxy dependency fault executor."""

from __future__ import annotations

import asyncio
import logging
import uuid

import httpx
from typing import Optional

from chaos_agent.config import get_settings
from chaos_agent.executors.base import AppliedResource, RollbackHandle
from chaos_agent.models import Fault

logger = logging.getLogger(__name__)

FAULT_TOXIC = {
    "dependency_blackhole": "timeout",
    "blackhole": "timeout",
    "timeout": "timeout",
    "latency": "latency",
    "slow": "latency",
    "connection_reset": "reset_peer",
}


class ToxiproxyExecutor:
    def __init__(self, simulate: Optional[bool] = None) -> None:
        self.simulate = simulate if simulate is not None else get_settings().simulate_execution
        self.base_url = get_settings().toxiproxy_url.rstrip("/")

    async def apply(
        self,
        experiment_id: str,
        fault: Fault,
        namespace: str,
        max_replica_percent: float,
    ) -> RollbackHandle:
        target = fault.target or "dependency"
        toxic_type = FAULT_TOXIC.get(fault.type, "latency")
        latency_ms = int(fault.params.get("latency_ms", 2000))
        proxy_name = f"chaos-{experiment_id[-8:]}-{target}"[:32]
        toxic_name = f"toxic-{uuid.uuid4().hex[:8]}"

        handle = RollbackHandle(
            experiment_id=experiment_id,
            executor="toxiproxy",
            simulated=self.simulate,
            resources=[
                AppliedResource(
                    api_version="toxiproxy/v1",
                    kind="Toxic",
                    namespace=namespace,
                    name=f"{proxy_name}/{toxic_name}",
                ),
            ],
        )

        if self.simulate:
            logger.info(
                "simulate_toxiproxy_apply",
                extra={"target": target, "type": toxic_type, "proxy": proxy_name},
            )
            return handle

        toxic_body: dict = {"type": toxic_type, "attributes": {}}
        if toxic_type == "latency":
            toxic_body["attributes"] = {"latency": latency_ms, "jitter": 100}
        if toxic_type == "timeout":
            toxic_body["attributes"] = {"timeout": 0}

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{self.base_url}/proxies/{proxy_name}/toxics", json=toxic_body)

        return handle

    async def rollback(self, handle: RollbackHandle) -> None:
        if handle.simulated:
            logger.info("simulate_toxiproxy_rollback", extra={"experiment_id": handle.experiment_id})
            return

        for resource in handle.resources:
            proxy, toxic = resource.name.split("/", 1)
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.delete(f"{self.base_url}/proxies/{proxy}/toxics/{toxic}")
            except Exception as exc:
                logger.warning("toxiproxy_rollback_failed", extra={"error": str(exc)})

    async def is_available(self) -> bool:
        if self.simulate:
            return True
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/version")
                return response.status_code == 200
        except Exception:
            return False
