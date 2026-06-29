"""Target contexts — cluster/namespace/AWS scope for collectors and compose."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from chaos_agent.config import get_settings
from chaos_agent.graph.provenance import snapshot_is_live, snapshot_provenance
from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import SnapshotContext

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "contexts.yaml"

_DEFAULT_CONTEXTS = [
    {
        "id": "eks-staging",
        "cluster": "eks-staging",
        "kube_context": "eks-staging",
        "namespace": "staging",
        "environment": "staging",
        "aws_account": "111122223333",
        "aws_region": "us-east-1",
        "label": "eks-staging / staging",
    },
    {
        "id": "eks-staging-platform",
        "cluster": "eks-staging",
        "kube_context": "eks-staging",
        "namespace": "platform",
        "environment": "staging",
        "aws_account": "111122223333",
        "aws_region": "us-east-1",
        "label": "eks-staging / platform",
    },
    {
        "id": "eks-prod",
        "cluster": "eks-prod",
        "kube_context": "eks-prod",
        "namespace": "production",
        "environment": "production",
        "aws_account": "111122223333",
        "aws_region": "us-east-1",
        "label": "eks-prod / production",
    },
]


def list_target_contexts() -> list[dict[str, Any]]:
    settings = get_settings()
    contexts = _load_config_contexts()
    default_ns = settings.default_namespace
    for ctx in contexts:
        ctx["is_default"] = ctx["namespace"] == default_ns
    return contexts


def get_context_by_id(context_id: str) -> dict[str, Any] | None:
    return next((c for c in list_target_contexts() if c["id"] == context_id), None)


def get_context_for_namespace(namespace: str) -> dict[str, Any] | None:
    return next((c for c in list_target_contexts() if c.get("namespace") == namespace), None)


def snapshot_builder_for_context(ctx: dict[str, Any]) -> SnapshotBuilder:
    return SnapshotBuilder(
        namespace=ctx.get("namespace", "staging"),
        kube_context=ctx.get("kube_context") or ctx.get("cluster"),
        aws_profile=ctx.get("aws_profile"),
        aws_region=ctx.get("aws_region"),
    )


def snapshot_builder_for_namespace(namespace: str = "staging", context_id: str | None = None) -> SnapshotBuilder:
    if context_id:
        ctx = get_context_by_id(context_id)
        if ctx:
            return snapshot_builder_for_context(ctx)
    ctx = get_context_for_namespace(namespace)
    if ctx:
        return snapshot_builder_for_context(ctx)
    return SnapshotBuilder(namespace)


def _load_config_contexts() -> list[dict[str, Any]]:
    if _CONFIG_PATH.exists():
        data = yaml.safe_load(_CONFIG_PATH.read_text()) or {}
        items = data.get("contexts", [])
        if items:
            return items
    settings = get_settings()
    contexts = [dict(c) for c in _DEFAULT_CONTEXTS]
    if settings.default_namespace:
        for ctx in contexts:
            if ctx["namespace"] == settings.default_namespace:
                ctx["is_default"] = True
    return contexts


async def probe_aws(namespace: str = "staging", context_id: str | None = None) -> dict[str, Any]:
    from chaos_agent.collectors.aws.collector import AwsCollector

    ctx = get_context_by_id(context_id) if context_id else get_context_for_namespace(namespace)
    collector = AwsCollector(
        profile=ctx.get("aws_profile") if ctx else None,
        region=ctx.get("aws_region") if ctx else None,
        namespace=namespace,
    )
    data = await collector.collect()
    expected_account = ctx.get("aws_account") if ctx else None
    live_account = data.get("account_id")
    account_match = expected_account is None or live_account == expected_account
    return {
        "source": data.get("source", "unknown"),
        "region": data.get("region"),
        "profile": data.get("profile"),
        "account_id": live_account,
        "expected_account": expected_account,
        "account_match": account_match if data.get("source") == "live" else None,
        "fallback_reason": data.get("fallback_reason"),
        "counts": {
            "rds": len(data.get("rds", [])),
            "load_balancers": len(data.get("load_balancers", [])),
            "sqs_queues": len(data.get("sqs_queues", [])),
            "elasticache": len(data.get("elasticache", [])),
        },
        "rds": data.get("rds", [])[:10],
        "sqs_queues": data.get("sqs_queues", [])[:10],
    }


async def probe_context(namespace: str, *, cluster: str = "eks-staging", context_id: str | None = None) -> dict[str, Any]:
    ctx = get_context_by_id(context_id) if context_id else get_context_for_namespace(namespace)
    if ctx:
        cluster = ctx.get("cluster", cluster)
        builder = snapshot_builder_for_context(ctx)
        snap_ctx = SnapshotContext(
            namespace=namespace,
            cluster=cluster,
            aws_account=ctx.get("aws_account", ""),
            aws_region=ctx.get("aws_region", "us-east-1"),
            environment=ctx.get("environment", "staging"),
        )
    else:
        builder = SnapshotBuilder(namespace, kube_context=cluster)
        snap_ctx = SnapshotContext(namespace=namespace, cluster=cluster)

    snapshot = await builder.build(snap_ctx)
    sources = snapshot_provenance(snapshot)
    aws_data = snapshot.aws
    return {
        "namespace": namespace,
        "cluster": cluster,
        "live_data": snapshot_is_live(snapshot),
        "collection_sources": sources,
        "services": [a.name for a in snapshot.applications],
        "dependencies": [d.name for d in snapshot.dependencies],
        "aws": {
            "source": aws_data.get("source"),
            "region": aws_data.get("region"),
            "account_id": aws_data.get("account_id"),
            "fallback_reason": aws_data.get("fallback_reason"),
            "rds_count": len(aws_data.get("rds", [])),
            "sqs_count": len(aws_data.get("sqs_queues", [])),
        },
    }
