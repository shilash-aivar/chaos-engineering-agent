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
        "namespace": "staging",
        "environment": "staging",
        "aws_account": "111122223333",
        "aws_region": "us-east-1",
        "label": "eks-staging / staging",
    },
    {
        "id": "eks-staging-platform",
        "cluster": "eks-staging",
        "namespace": "platform",
        "environment": "staging",
        "aws_account": "111122223333",
        "aws_region": "us-east-1",
        "label": "eks-staging / platform",
    },
    {
        "id": "eks-prod",
        "cluster": "eks-prod",
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


async def probe_context(namespace: str, *, cluster: str = "eks-staging") -> dict[str, Any]:
    builder = SnapshotBuilder(namespace)
    snapshot = await builder.build(SnapshotContext(namespace=namespace, cluster=cluster))
    sources = snapshot_provenance(snapshot)
    return {
        "namespace": namespace,
        "cluster": cluster,
        "live_data": snapshot_is_live(snapshot),
        "collection_sources": sources,
        "services": [a.name for a in snapshot.applications],
        "dependencies": [d.name for d in snapshot.dependencies],
    }
