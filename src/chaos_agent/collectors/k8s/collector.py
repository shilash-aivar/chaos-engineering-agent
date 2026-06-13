"""K8s collector — deployments, services, posture signals."""

from __future__ import annotations

from typing import Any


class K8sCollector:
    def __init__(self, namespace: str = "staging") -> None:
        self.namespace = namespace

    async def collect(self) -> dict[str, Any]:
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
        }
