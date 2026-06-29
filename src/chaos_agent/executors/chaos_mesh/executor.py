"""Chaos Mesh fault injection via Kubernetes custom resources."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from chaos_agent.config import get_settings
from chaos_agent.executors.base import AppliedResource, RollbackHandle, fault_label_selector
from chaos_agent.models import Fault

logger = logging.getLogger(__name__)

CHAOS_GROUP = "chaos-mesh.org"
CHAOS_VERSION = "v1alpha1"


class ChaosMeshExecutor:
    def __init__(self, simulate: Optional[bool] = None) -> None:
        self.simulate = simulate if simulate is not None else get_settings().simulate_execution

    def _custom_api(self, kube_context: str | None = None) -> Any:
        from kubernetes import client
        from chaos_agent.platform.kube import load_kubernetes_config

        load_kubernetes_config(kube_context)
        return client.CustomObjectsApi()

    def _resource_name(self, experiment_id: str, fault_type: str) -> str:
        safe = experiment_id.replace("_", "-").lower()[:40]
        return f"chaos-agent-{safe}-{fault_type.replace('_', '-')}"[:63]

    def _pod_chaos_body(
        self,
        name: str,
        namespace: str,
        target: str,
        max_percent: float,
        duration: str,
    ) -> dict[str, Any]:
        mode = "fixed-percent"
        value = str(int(min(max_percent, 30)))
        if max_percent <= 0:
            mode = "one"
            value = "1"
        return {
            "apiVersion": f"{CHAOS_GROUP}/{CHAOS_VERSION}",
            "kind": "PodChaos",
            "metadata": {"name": name, "namespace": namespace},
            "spec": {
                "action": "pod-kill",
                "mode": mode,
                "value": value,
                "duration": duration,
                "selector": {"labelSelectors": fault_label_selector(target)},
            },
        }

    def _network_chaos_body(
        self,
        name: str,
        namespace: str,
        target: str,
        latency_ms: int,
        duration: str,
    ) -> dict[str, Any]:
        return {
            "apiVersion": f"{CHAOS_GROUP}/{CHAOS_VERSION}",
            "kind": "NetworkChaos",
            "metadata": {"name": name, "namespace": namespace},
            "spec": {
                "action": "delay",
                "mode": "one",
                "duration": duration,
                "selector": {"labelSelectors": fault_label_selector(target)},
                "delay": {"latency": f"{latency_ms}ms"},
            },
        }

    async def apply(
        self,
        experiment_id: str,
        fault: Fault,
        namespace: str,
        max_replica_percent: float,
        *,
        kube_context: str | None = None,
    ) -> RollbackHandle:
        target = fault.target or "app"
        duration = fault.params.get("duration", "120s")
        handle = RollbackHandle(
            experiment_id=experiment_id,
            executor="chaos_mesh",
            simulated=self.simulate,
        )

        if fault.type in ("pod_kill", "pod-kill"):
            kind = "PodChaos"
            body = self._pod_chaos_body(
                self._resource_name(experiment_id, "pod-kill"),
                namespace,
                target,
                max_replica_percent,
                str(duration),
            )
        elif fault.type in ("network_latency", "network-latency"):
            kind = "NetworkChaos"
            latency_ms = int(fault.params.get("latency_ms", 500))
            body = self._network_chaos_body(
                self._resource_name(experiment_id, "network"),
                namespace,
                target,
                latency_ms,
                str(duration),
            )
        else:
            raise ValueError(f"unsupported chaos_mesh fault type: {fault.type}")

        name = body["metadata"]["name"]
        handle.resources.append(
            AppliedResource(
                api_version=f"{CHAOS_GROUP}/{CHAOS_VERSION}",
                kind=kind,
                namespace=namespace,
                name=name,
            ),
        )

        if self.simulate:
            logger.info("simulate_chaos_apply", extra={"kind": kind, "name": name})
            return handle

        plural = "podchaos" if kind == "PodChaos" else "networkchaos"
        await asyncio.to_thread(
            self._custom_api(kube_context).create_namespaced_custom_object,
            CHAOS_GROUP,
            CHAOS_VERSION,
            namespace,
            plural,
            body,
        )
        return handle

    async def rollback(self, handle: RollbackHandle, *, kube_context: str | None = None) -> None:
        if handle.simulated:
            logger.info("simulate_chaos_rollback", extra={"experiment_id": handle.experiment_id})
            return

        api = self._custom_api(kube_context)
        for resource in handle.resources:
            plural = "podchaos" if resource.kind == "PodChaos" else "networkchaos"
            try:
                await asyncio.to_thread(
                    api.delete_namespaced_custom_object,
                    CHAOS_GROUP,
                    CHAOS_VERSION,
                    resource.namespace,
                    plural,
                    resource.name,
                )
            except Exception as exc:
                logger.warning(
                    "chaos_rollback_delete_failed",
                    extra={"name": resource.name, "error": str(exc)},
                )

    async def is_available(self) -> bool:
        if self.simulate:
            return True
        try:
            await asyncio.to_thread(self._custom_api)
            return True
        except Exception:
            return False
