"""Application-layer collector — services, health paths, resilience config."""

from __future__ import annotations

from chaos_agent.graph.types import AppService


class AppCollector:
    def __init__(self, namespace: str = "staging") -> None:
        self.namespace = namespace

    async def collect(self) -> list[AppService]:
        # Phase 1: seed data; later parse Deployments, env, feature-flag CRDs
        return [
            AppService(
                name="checkout",
                namespace=self.namespace,
                tier="critical",
                health_path="/health",
                has_circuit_breaker=False,
                has_retry=False,
                feature_flags=["checkout-v2", "degraded-payments"],
            ),
            AppService(
                name="payments-api",
                namespace=self.namespace,
                tier="critical",
                health_path="/healthz",
                has_circuit_breaker=False,
                has_retry=True,
            ),
            AppService(
                name="inventory-api",
                namespace=self.namespace,
                tier="standard",
                health_path="/health",
                has_retry=False,
            ),
        ]
