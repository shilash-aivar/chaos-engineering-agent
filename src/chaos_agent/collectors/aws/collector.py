"""AWS collector — live boto3 with seed fallback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from chaos_agent.platform.aws import boto_session, resolve_aws_config

logger = logging.getLogger(__name__)


class AwsCollector:
    def __init__(
        self,
        profile: Optional[str] = None,
        region: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> None:
        self.profile = profile
        self.region = region
        self.namespace = namespace

    def _seed(self) -> dict[str, Any]:
        _, reg = resolve_aws_config(profile=self.profile, region=self.region, namespace=self.namespace)
        return {
            "rds": [
                {"id": "payments-db", "multi_az": False, "tier": "critical", "engine": "postgres"},
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
            "region": reg,
            "account_id": None,
            "source": "seed",
        }

    def _collect_sync(self) -> dict[str, Any]:
        from botocore.config import Config

        prof, region = resolve_aws_config(
            profile=self.profile,
            region=self.region,
            namespace=self.namespace,
        )
        session = boto_session(profile=prof, region=region, namespace=self.namespace)
        cfg = Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1})

        sts = session.client("sts", config=cfg)
        account_id = sts.get_caller_identity().get("Account")

        rds = session.client("rds", region_name=region, config=cfg)
        elbv2 = session.client("elbv2", region_name=region, config=cfg)
        sqs = session.client("sqs", region_name=region, config=cfg)
        elasticache = session.client("elasticache", region_name=region, config=cfg)

        rds_items = []
        for inst in rds.describe_db_instances().get("DBInstances", [])[:30]:
            ident = inst.get("DBInstanceIdentifier", "unknown")
            rds_items.append(
                {
                    "id": ident,
                    "multi_az": bool(inst.get("MultiAZ")),
                    "engine": inst.get("Engine"),
                    "tier": "critical" if any(k in ident.lower() for k in ("payment", "order", "auth")) else "standard",
                },
            )

        lb_items = []
        for lb in elbv2.describe_load_balancers().get("LoadBalancers", [])[:30]:
            lb_items.append({"name": lb.get("LoadBalancerName", "unknown"), "health_check_path": "/"})

        queue_items = []
        for url in sqs.list_queues().get("QueueUrls", [])[:30]:
            name = url.rsplit("/", 1)[-1]
            attrs = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["All"]).get("Attributes", {})
            queue_items.append(
                {
                    "name": name,
                    "dlq": "RedrivePolicy" in attrs,
                    "tier": "critical" if any(k in name.lower() for k in ("order", "payment", "event")) else "standard",
                },
            )

        cache_items = []
        for cluster in elasticache.describe_cache_clusters().get("CacheClusters", [])[:30]:
            cache_items.append(
                {
                    "name": cluster.get("CacheClusterId", "unknown"),
                    "cluster_mode": bool(cluster.get("ReplicationGroupId")),
                },
            )

        return {
            "rds": rds_items,
            "load_balancers": lb_items,
            "sqs_queues": queue_items,
            "elasticache": cache_items,
            "region": region,
            "account_id": account_id,
            "profile": prof,
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
