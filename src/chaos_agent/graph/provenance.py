"""Snapshot provenance helpers."""

from __future__ import annotations

from chaos_agent.graph.types import InfraSnapshot


def snapshot_provenance(snapshot: InfraSnapshot) -> dict[str, str]:
    return {
        "kubernetes": snapshot.kubernetes.get("source", "unknown"),
        "aws": snapshot.aws.get("source", "unknown"),
        "applications": "catalog",
        "dependencies": "catalog",
        "observability": "live",
        "graph_edges": "catalog",
    }


def snapshot_is_live(snapshot: InfraSnapshot) -> bool:
    sources = snapshot_provenance(snapshot)
    return sources["kubernetes"] == "live" and sources["aws"] == "live"
