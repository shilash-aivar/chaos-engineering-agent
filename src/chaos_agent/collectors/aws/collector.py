"""AWS collector — RDS, ELB, SQS, ElastiCache."""

from __future__ import annotations

from typing import Any


class AwsCollector:
    async def collect(self) -> dict[str, Any]:
        return {
            "rds": [
                {"id": "payments-db", "multi_az": False, "tier": "critical"},
            ],
            "load_balancers": [
                {"name": "checkout-alb", "health_check_path": "/"},
            ],
            "sqs_queues": [
                {"name": "order-events", "dlq": False, "tier": "critical"},
            ],
            "elasticache": [
                {"name": "session-cache", "cluster_mode": False},
            ],
        }
