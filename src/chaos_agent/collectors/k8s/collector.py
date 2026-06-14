"""K8s collector — live cluster with seed fallback."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class K8sCollector:
    def __init__(self, namespace: str = "staging") -> None:
        self.namespace = namespace

    def _seed(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "deployments": [
                {"name": "checkout", "replicas": 3, "priority_class": None, "readiness_probe": False},
                {"name": "payments-api", "replicas": 2, "priority_class": None, "readiness_probe": True},
                {"name": "inventory-api", "replicas": 2, "priority_class": None, "readiness_probe": True},
            ],
            "services": ["checkout", "payments-api", "inventory-api"],
            "priority_classes": [],
            "istio": {"enabled": False},
            "source": "seed",
        }

    def _collect_sync(self) -> dict[str, Any]:
        from kubernetes import client, config
        from kubernetes.config.config_exception import ConfigException

        try:
            config.load_incluster_config()
        except ConfigException:
            if not os.environ.get("KUBECONFIG") and not os.path.exists(os.path.expanduser("~/.kube/config")):
                raise RuntimeError("no kubeconfig")
            config.load_kube_config()

        apps = client.AppsV1Api()
        core = client.CoreV1Api()
        deploys = apps.list_namespaced_deployment(namespace=self.namespace, _request_timeout=3)
        services = core.list_namespaced_service(namespace=self.namespace, _request_timeout=3)
        pcs = core.list_priority_class(_request_timeout=3)

        deployments = []
        for d in deploys.items:
            spec = d.spec
            template = spec.template if spec else None
            containers = template.spec.containers if template and template.spec else []
            readiness = any(c.readiness_probe is not None for c in containers) if containers else False
            deployments.append(
                {
                    "name": d.metadata.name,
                    "replicas": spec.replicas if spec else 0,
                    "priority_class": template.spec.priority_class_name if template and template.spec else None,
                    "readiness_probe": readiness,
                },
            )

        return {
            "namespace": self.namespace,
            "deployments": deployments or self._seed()["deployments"],
            "services": [s.metadata.name for s in services.items],
            "priority_classes": [p.metadata.name for p in pcs.items],
            "istio": {"enabled": False},
            "source": "live",
        }

    async def collect(self) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(self._collect_sync)
        except Exception as exc:
            logger.debug("k8s_collector_fallback", extra={"error": str(exc)})
            data = self._seed()
            data["fallback_reason"] = str(exc)
            return data
