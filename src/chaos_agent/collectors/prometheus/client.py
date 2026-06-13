"""Prometheus HTTP query client."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from chaos_agent.config import get_settings

logger = logging.getLogger(__name__)

# Built-in PromQL templates keyed by watch_metrics aliases
METRIC_QUERIES: dict[str, str] = {
    "error_rate": 'sum(rate(http_requests_total{status=~"5.."}[2m]))',
    "latency_p99": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[2m])) by (le))",
    "checkout_error_rate": 'sum(rate(http_requests_total{service="checkout",status=~"5.."}[2m]))',
    "checkout_p99": (
        'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service="checkout"}[2m])) by (le))'
    ),
    "payments_error_rate": 'sum(rate(http_requests_total{service="payments-api",status=~"5.."}[2m]))',
    "payments_p99": (
        'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service="payments-api"}[2m])) by (le))'
    ),
    "inventory_upstream_errors": 'sum(rate(http_requests_total{service="inventory-api",status=~"5.."}[2m]))',
    "db_connection_errors": "sum(rate(db_connection_errors_total[2m]))",
}


class PrometheusClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or get_settings().prometheus_url).rstrip("/")

    async def query(self, promql: str) -> Optional[float]:
        url = f"{self.base_url}/api/v1/query"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params={"query": promql})
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except Exception as exc:
            logger.warning("prometheus_query_failed", extra={"error": str(exc), "query": promql})
            return None

        if payload.get("status") != "success":
            return None

        result = payload.get("data", {}).get("result", [])
        if not result:
            return 0.0

        value = result[0].get("value", [None, "0"])
        try:
            return float(value[1])
        except (TypeError, ValueError, IndexError):
            return None

    async def snapshot(self, metric_names: list[str]) -> dict[str, float]:
        values: dict[str, float] = {}
        for name in metric_names:
            promql = METRIC_QUERIES.get(name, METRIC_QUERIES["error_rate"])
            result = await self.query(promql)
            if result is not None:
                values[name] = result
        return values

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/-/healthy")
                return response.status_code == 200
        except Exception:
            return False
