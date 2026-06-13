"""Dependency collector — DB, cache, queues, third-party HTTP/gRPC."""

from __future__ import annotations

from chaos_agent.graph.types import Dependency


class DependencyCollector:
    def __init__(self, namespace: str = "staging") -> None:
        self.namespace = namespace

    async def collect(self) -> list[Dependency]:
        return [
            Dependency(
                name="payments-db",
                type="postgres",
                owner_service="payments-api",
                endpoint="payments-db.staging.svc:5432",
                has_timeout=False,
                has_retry=False,
                pool_size=10,
            ),
            Dependency(
                name="session-cache",
                type="redis",
                owner_service="checkout",
                endpoint="redis.staging.svc:6379",
                has_timeout=True,
                has_retry=False,
            ),
            Dependency(
                name="order-events",
                type="kafka",
                owner_service="checkout",
                endpoint="kafka.staging.svc:9092/order-events",
                has_timeout=True,
                has_retry=False,
            ),
            Dependency(
                name="stripe-api",
                type="http",
                owner_service="payments-api",
                endpoint="https://api.stripe.com",
                has_timeout=True,
                has_retry=False,
                third_party=True,
            ),
            Dependency(
                name="auth0",
                type="http",
                owner_service="checkout",
                endpoint="https://tenant.auth0.com",
                has_timeout=False,
                has_retry=False,
                third_party=True,
            ),
        ]
