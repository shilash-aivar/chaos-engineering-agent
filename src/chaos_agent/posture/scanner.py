"""Posture rule scanner across k8s, aws, app, deps, observability."""

from __future__ import annotations

import time
from typing import Any, Literal

from chaos_agent.graph.provenance import snapshot_is_live, snapshot_provenance
from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import InfraSnapshot

PostureScope = Literal["k8s", "aws", "app", "deps", "observability"]

_SCAN_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 60


class PostureScanner:
    def __init__(self, namespace: str = "staging") -> None:
        self.builder = SnapshotBuilder(namespace)

    async def scan(self) -> dict[str, Any]:
        cache_key = self.builder.namespace
        cached = _SCAN_CACHE.get(cache_key)
        if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
            return cached[1]

        snapshot = await self.builder.build()
        gaps = self._evaluate(snapshot)
        result = {
            "gaps": gaps,
            "scanned_at": snapshot.captured_at.isoformat(),
            "collection_sources": snapshot_provenance(snapshot),
            "live_data": snapshot_is_live(snapshot),
            "summary": {
                "k8s": sum(1 for g in gaps if g["scope"] == "k8s"),
                "aws": sum(1 for g in gaps if g["scope"] == "aws"),
                "app": sum(1 for g in gaps if g["scope"] == "app"),
                "deps": sum(1 for g in gaps if g["scope"] == "deps"),
                "observability": sum(1 for g in gaps if g["scope"] == "observability"),
            },
        }
        _SCAN_CACHE[cache_key] = (time.monotonic(), result)
        return result

    def _evaluate(self, snapshot: InfraSnapshot) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        gap_id = 0

        for dep in snapshot.kubernetes.get("deployments", []):
            if dep.get("name") in ("checkout", "payments-api") and not dep.get("priority_class"):
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "k8s",
                        "critical",
                        dep["name"],
                        "critical-pods-priority-class",
                        "Critical deployment has no PriorityClass",
                        "Create chaos-critical PriorityClass and patch deployment",
                    ),
                )
            if dep.get("name") == "checkout" and not dep.get("readiness_probe"):
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "k8s",
                        "high",
                        dep["name"],
                        "critical-deployment-probes",
                        "Missing readiness probe",
                        "Add httpGet /health readiness probe",
                    ),
                )

        for rds in snapshot.aws.get("rds", []):
            if not rds.get("multi_az"):
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "aws",
                        "critical",
                        rds["id"],
                        "critical-rds-multi-az",
                        "RDS instance is single-AZ",
                        "Terraform PR: multi_az = true",
                    ),
                )

        for queue in snapshot.aws.get("sqs_queues", []):
            if not queue.get("dlq"):
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "aws",
                        "high",
                        queue["name"],
                        "critical-sqs-dlq",
                        "Critical SQS queue has no DLQ",
                        "Add dead-letter queue and alarm on oldest message age",
                    ),
                )

        for app in snapshot.applications:
            if app.tier == "critical" and not app.has_circuit_breaker:
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "app",
                        "high",
                        app.name,
                        "app-circuit-breaker",
                        "Critical app has no circuit breaker on upstream calls",
                        "Add Istio outlier detection or Resilience4j circuit breaker",
                    ),
                )
            if not app.has_retry and app.tier == "critical":
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "app",
                        "medium",
                        app.name,
                        "app-retry-policy",
                        "No retry policy on outbound HTTP/gRPC",
                        "Add retry: attempts=3, perTryTimeout=2s",
                    ),
                )

        for dep in snapshot.dependencies:
            if dep.type == "postgres" and (dep.pool_size or 0) < 20:
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "deps",
                        "critical",
                        dep.name,
                        "deps-db-pool-size",
                        f"Connection pool size {dep.pool_size} is low for {dep.owner_service}",
                        "Increase pool to 25; add connection timeout 3s",
                    ),
                )
            if dep.third_party and not dep.has_timeout:
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "deps",
                        "high",
                        dep.name,
                        "deps-third-party-timeout",
                        f"Third-party {dep.name} has no client timeout",
                        "Set HTTP client timeout 5s with bounded retry",
                    ),
                )
            if dep.type == "redis" and not dep.has_retry:
                gap_id += 1
                gaps.append(
                    self._gap(
                        gap_id,
                        "deps",
                        "medium",
                        dep.name,
                        "deps-cache-fallback",
                        "No cache fallback when Redis unavailable",
                        "Add stale-while-revalidate or in-memory fallback",
                    ),
                )

        for obs in snapshot.observability:
            if obs.status != "ok":
                gap_id += 1
                severity = "critical" if obs.name == "prometheus" else "high"
                gaps.append(
                    self._gap(
                        gap_id,
                        "observability",
                        severity,
                        obs.name,
                        f"obs-{obs.name}",
                        obs.detail or f"{obs.name} not configured",
                        self._obs_remediation(obs.name),
                    ),
                )

        return gaps

    @staticmethod
    def _gap(
        gap_id: int,
        scope: PostureScope,
        severity: str,
        service: str,
        rule: str,
        message: str,
        remediation: str,
    ) -> dict[str, Any]:
        return {
            "id": f"gap-{gap_id}",
            "scope": scope,
            "severity": severity,
            "service": service,
            "rule": rule,
            "message": message,
            "remediation": remediation,
        }

    @staticmethod
    def _obs_remediation(name: str) -> str:
        mapping = {
            "prometheus": "Install kube-prometheus-stack; scrape checkout and payments",
            "tempo": "Add OpenTelemetry SDK span on checkout→payments outbound call",
            "pagerduty": "Set PAGERDUTY_API_KEY for incident replay scenarios",
            "github": "Set GITHUB_TOKEN for auto-ticket creation",
            "grafana": "Deploy Grafana or fix GRAFANA_URL connectivity",
        }
        return mapping.get(name, "Configure observability integration")
