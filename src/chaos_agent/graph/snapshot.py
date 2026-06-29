"""Build unified infra snapshot from all collectors."""

from __future__ import annotations

import asyncio
from typing import Optional

from chaos_agent.collectors.app.collector import AppCollector
from chaos_agent.collectors.aws.collector import AwsCollector
from chaos_agent.collectors.deps.collector import DependencyCollector
from chaos_agent.collectors.k8s.collector import K8sCollector
from chaos_agent.collectors.observability.collector import ObservabilityCollector
from chaos_agent.graph.types import GraphEdge, GraphEdgeType, InfraSnapshot, SnapshotContext

_COLLECTOR_TIMEOUT_SECONDS = 4


class SnapshotBuilder:
    def __init__(
        self,
        namespace: str = "staging",
        kube_context: str | None = None,
        aws_profile: str | None = None,
        aws_region: str | None = None,
    ) -> None:
        self.namespace = namespace
        self.k8s = K8sCollector(namespace, kube_context=kube_context)
        self.aws = AwsCollector(profile=aws_profile, region=aws_region, namespace=namespace)
        self.app = AppCollector(namespace)
        self.deps = DependencyCollector(namespace)
        self.obs = ObservabilityCollector()

    async def _collect_bounded(self, coro, fallback):
        try:
            return await asyncio.wait_for(coro, timeout=_COLLECTOR_TIMEOUT_SECONDS)
        except Exception:
            return fallback

    async def build(self, context: Optional[SnapshotContext] = None) -> InfraSnapshot:
        ctx = context or SnapshotContext(namespace=self.namespace)

        apps, dependencies, observability, k8s_data, aws_data = await asyncio.gather(
            self._collect_bounded(self.app.collect(), []),
            self._collect_bounded(self.deps.collect(), []),
            self._collect_bounded(self.obs.collect(), []),
            self._collect_bounded(self.k8s.collect(), self.k8s._seed()),
            self._collect_bounded(self.aws.collect(), self.aws._seed()),
        )

        edges: list[GraphEdge] = [
            GraphEdge.model_validate({"from": "ingress", "to": "checkout", "type": "ingress"}),
            GraphEdge.model_validate({"from": "checkout", "to": "payments-api", "type": "k8s_service"}),
            GraphEdge.model_validate({"from": "checkout", "to": "inventory-api", "type": "k8s_service"}),
            GraphEdge.model_validate({"from": "payments-api", "to": "payments-db", "type": "rds"}),
            GraphEdge.model_validate({"from": "checkout", "to": "order-events", "type": "sqs"}),
            GraphEdge.model_validate({"from": "checkout", "to": "session-cache", "type": "cache"}),
            GraphEdge.model_validate({"from": "payments-api", "to": "stripe-api", "type": "http_api"}),
            GraphEdge.model_validate({"from": "checkout", "to": "auth0", "type": "http_api"}),
            GraphEdge.model_validate({"from": "order-events", "to": "fulfillment-kafka", "type": "kafka"}),
        ]

        return InfraSnapshot(
            context=ctx,
            kubernetes=k8s_data,
            aws=aws_data,
            applications=apps,
            dependencies=dependencies,
            observability=observability,
            graph_edges=edges,
        )

    def evidence_lines(self, snapshot: InfraSnapshot) -> list[str]:
        lines: list[str] = []
        for app in snapshot.applications:
            if not app.has_retry:
                lines.append(f"{app.name}: no retry configured")
            if not app.has_circuit_breaker and app.tier == "critical":
                lines.append(f"{app.name}: no circuit breaker (critical tier)")
        for dep in snapshot.dependencies:
            if not dep.has_timeout:
                lines.append(f"{dep.owner_service}→{dep.name}: no timeout on {dep.type}")
            if dep.type == "postgres" and (dep.pool_size or 0) < 20:
                lines.append(f"{dep.name}: connection pool size {dep.pool_size or 'unset'} (low)")
        for obs in snapshot.observability:
            if obs.status != "ok":
                lines.append(f"observability/{obs.name}: {obs.detail or obs.status}")
        return lines
