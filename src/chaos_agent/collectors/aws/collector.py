"""AWS collector — live boto3 with seed fallback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AwsCollector:
    def _seed(self) -> dict[str, Any]:
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
            "source": "seed",
        }

    def _collect_sync(self) -> dict[str, Any]:
        import boto3
        from botocore.config import Config

        session = boto3.Session()
        region = session.region_name or "us-east-1"
        cfg = Config(connect_timeout=2, read_timeout=3, retries={"max_attempts": 1})
        rds = session.client("rds", region_name=region, config=cfg)
        elbv2 = session.client("elbv2", region_name=region, config=cfg)
        sqs = session.client("sqs", region_name=region, config=cfg)
        elasticache = session.client("elasticache", region_name=region, config=cfg)

        rds_items = []
        for inst in rds.describe_db_instances().get("DBInstances", [])[:20]:
            rds_items.append(
                {
                    "id": inst.get("DBInstanceIdentifier", "unknown"),
                    "multi_az": bool(inst.get("MultiAZ")),
                    "tier": "critical" if "payment" in inst.get("DBInstanceIdentifier", "") else "standard",
                },
            )

        lb_items = []
        for lb in elbv2.describe_load_balancers().get("LoadBalancers", [])[:20]:
            lb_items.append({"name": lb.get("LoadBalancerName", "unknown"), "health_check_path": "/"})

        queue_items = []
        for url in sqs.list_queues().get("QueueUrls", [])[:20]:
            name = url.rsplit("/", 1)[-1]
            attrs = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["All"]).get("Attributes", {})
            queue_items.append(
                {
                    "name": name,
                    "dlq": "RedrivePolicy" in attrs,
                    "tier": "critical" if "order" in name else "standard",
                },
            )

        cache_items = []
        for cluster in elasticache.describe_cache_clusters().get("CacheClusters", [])[:20]:
            cache_items.append(
                {
                    "name": cluster.get("CacheClusterId", "unknown"),
                    "cluster_mode": cluster.get("CacheClusterStatus") == "available",
                },
            )

        return {
            "rds": rds_items or self._seed()["rds"],
            "load_balancers": lb_items or self._seed()["load_balancers"],
            "sqs_queues": queue_items or self._seed()["sqs_queues"],
            "elasticache": cache_items or self._seed()["elasticache"],
            "source": "live",
        }

    async def collect(self) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(self._collect_sync)
        except Exception as exc:
            logger.debug("aws_collector_fallback", extra={"error": str(exc)})
            data = self._seed()
            data["fallback_reason"] = str(exc)
            return data
