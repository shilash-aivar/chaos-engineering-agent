"""Tools the context agent can call to read live and declared context."""

from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

from chaos_agent.context.understanding import understanding_from_snapshot
from chaos_agent.graph.provenance import snapshot_is_live, snapshot_provenance
from chaos_agent.graph.types import SnapshotContext
from chaos_agent.platform.integrations_service import get_integrations_status
from chaos_agent.platform.target_context_service import (
    get_context_by_id,
    get_context_for_namespace,
    probe_aws,
    probe_context,
    snapshot_builder_for_namespace,
)
from chaos_agent.posture.scanner import PostureScanner
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.context import ContextRepository


ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "get_live_snapshot",
            "description": "Collect the five-ring infrastructure snapshot: K8s, AWS, apps, deps, observability.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "probe_aws",
            "description": "Probe AWS in the target region: RDS, SQS, ELB, ElastiCache, account id.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "probe_target",
            "description": "Probe target context: collection sources, services, AWS summary.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_posture_gaps",
            "description": "Run posture rules against the live snapshot and return gaps by scope.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_declared_context",
            "description": "Get latest ingested declared context (Terraform, docs, manifests) if any.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_context_analysis",
            "description": "Get declared-vs-observed context analysis gaps and blue suggestions if ingested.",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "get_integrations",
            "description": "List integration connector status (K8s, AWS, Prometheus, GitHub, etc.).",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "finish_understanding",
            "description": "Submit final grounded understanding. Call only when ready.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Executive summary (2-4 sentences)"},
                    "infrastructure_overview": {
                        "type": "string",
                        "description": "Structured overview of observed infrastructure",
                    },
                    "problem_framing": {
                        "type": "string",
                        "description": "How the problem statement maps to this environment",
                    },
                    "top_risks": {"type": "array", "items": {"type": "string"}},
                    "recommended_chaos_focus": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "data_gaps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "infrastructure_overview", "problem_framing", "confidence"],
            },
        },
    ]


class ContextToolRegistry:
    def __init__(self, namespace: str, context_id: str | None = None) -> None:
        self.namespace = namespace
        self.context_id = context_id
        ctx = get_context_by_id(context_id) if context_id else get_context_for_namespace(namespace)
        self._ctx = ctx

    async def execute(self, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        handlers: dict[str, ToolHandler] = {
            "get_live_snapshot": self._get_live_snapshot,
            "probe_aws": self._probe_aws,
            "probe_target": self._probe_target,
            "get_posture_gaps": self._get_posture_gaps,
            "get_declared_context": self._get_declared_context,
            "get_context_analysis": self._get_context_analysis,
            "get_integrations": self._get_integrations,
        }
        if name == "finish_understanding":
            return {"status": "finished", **tool_input}
        handler = handlers.get(name)
        if handler is None:
            return {"error": f"unknown tool: {name}"}
        try:
            return await handler(**tool_input)
        except Exception as exc:
            return {"error": str(exc)}

    async def _get_live_snapshot(self, **_kwargs: Any) -> dict[str, Any]:
        builder = snapshot_builder_for_namespace(self.namespace, self.context_id)
        ctx = self._ctx or {}
        snapshot = await builder.build(
            SnapshotContext(
                namespace=self.namespace,
                cluster=ctx.get("cluster", "eks-staging"),
                aws_account=ctx.get("aws_account", ""),
                aws_region=ctx.get("aws_region", "us-east-1"),
                environment=ctx.get("environment", "staging"),
            ),
        )
        return {
            "live_data": snapshot_is_live(snapshot),
            "collection_sources": snapshot_provenance(snapshot),
            "applications": [a.model_dump() for a in snapshot.applications],
            "dependencies": [d.model_dump() for d in snapshot.dependencies],
            "kubernetes": snapshot.kubernetes,
            "aws": snapshot.aws,
            "observability": [o.model_dump() for o in snapshot.observability],
            "evidence_hints": builder.evidence_lines(snapshot)[:15],
        }

    async def _probe_aws(self, **_kwargs: Any) -> dict[str, Any]:
        return await probe_aws(self.namespace, context_id=self.context_id)

    async def _probe_target(self, **_kwargs: Any) -> dict[str, Any]:
        cluster = (self._ctx or {}).get("cluster", "eks-staging")
        return await probe_context(self.namespace, cluster=cluster, context_id=self.context_id)

    async def _get_posture_gaps(self, **_kwargs: Any) -> dict[str, Any]:
        scanner = PostureScanner(self.namespace)
        scanner.builder = snapshot_builder_for_namespace(self.namespace, self.context_id)
        return await scanner.scan()

    async def _get_declared_context(self, **_kwargs: Any) -> dict[str, Any]:
        factory = get_session_factory()
        async with factory() as session:
            repo = ContextRepository(session)
            row = await repo.get_latest(self.namespace)
            if row is None:
                return {"found": False, "message": "No declared context ingested"}
            snap = ContextRepository.row_to_snapshot(row)
            builder = snapshot_builder_for_namespace(self.namespace, self.context_id)
            infra = await builder.build()
            understanding = understanding_from_snapshot(snap, infra)
            return {
                "found": True,
                "snapshot_id": snap.id,
                "repo_name": snap.repo_name,
                "ingested_at": snap.ingested_at.isoformat(),
                "terraform_resources": len(snap.declared.terraform_resources),
                "documents": len(snap.declared.documents),
                "manifest_files": len(snap.declared.manifest_sources),
                "code_files": len(snap.declared.code_sources),
                "claims": [c for d in snap.declared.documents for c in d.claims],
                "understanding": understanding,
            }

    async def _get_context_analysis(self, **_kwargs: Any) -> dict[str, Any]:
        factory = get_session_factory()
        async with factory() as session:
            repo = ContextRepository(session)
            row = await repo.get_latest(self.namespace)
            if row is None:
                return {"found": False}
            analysis = ContextRepository.analysis_from_row(row)
            if analysis is None:
                analysis = await repo.run_analysis(row)
            return {
                "found": True,
                "gaps": [g.model_dump() for g in analysis.gaps[:20]],
                "blue_suggestions": [s.model_dump() for s in analysis.blue_suggestions[:10]],
                "posture_summary": analysis.posture_summary,
                "declared_summary": analysis.declared_summary,
            }

    async def _get_integrations(self, **_kwargs: Any) -> dict[str, Any]:
        integrations = await get_integrations_status()
        return {
            "integrations": [
                {"id": i["id"], "name": i["name"], "status": i["status"], "detail": i["detail"]}
                for i in integrations
            ],
        }


def truncate_tool_result(data: dict[str, Any], max_chars: int = 12_000) -> str:
    text = json.dumps(data, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…[truncated]"
