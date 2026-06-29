"""Context agent loop — tool-use until grounded understanding."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from chaos_agent.context.agent.prompts import CONTEXT_AGENT_SYSTEM
from chaos_agent.context.agent.tools import ContextToolRegistry, tool_definitions, truncate_tool_result
from chaos_agent.llm.client import get_llm_client
from chaos_agent.platform.target_context_service import get_context_by_id, get_context_for_namespace

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 8


async def run_context_agent(
    *,
    problem_statement: str,
    namespace: str = "staging",
    context_id: str | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> dict[str, Any]:
    """Run the context understanding agent loop. Returns summary + tool trace."""
    registry = ContextToolRegistry(namespace, context_id)
    ctx = get_context_by_id(context_id) if context_id else get_context_for_namespace(namespace)
    target_label = ctx.get("label", f"{namespace}") if ctx else namespace

    llm = get_llm_client()
    if not llm.available:
        return await _rules_fallback(
            registry=registry,
            problem_statement=problem_statement,
            namespace=namespace,
            target_label=target_label,
        )

    initial_user = _build_initial_message(problem_statement, namespace, target_label, ctx)
    messages: list[dict[str, Any]] = [{"role": "user", "content": initial_user}]
    tool_trace: list[dict[str, Any]] = []
    tools = tool_definitions()

    for iteration in range(1, max_iterations + 1):
        response = await llm.complete_with_tools(
            system=CONTEXT_AGENT_SYSTEM,
            messages=messages,
            tools=tools,
            max_tokens=4096,
        )
        if response is None:
            return await _rules_fallback(
                registry=registry,
                problem_statement=problem_statement,
                namespace=namespace,
                target_label=target_label,
                tool_trace=tool_trace,
                reason="llm_call_failed",
            )

        assistant_content = response["content"]
        messages.append({"role": "assistant", "content": assistant_content})

        tool_uses = [b for b in assistant_content if b.get("type") == "tool_use"]
        if not tool_uses:
            text_blocks = [b.get("text", "") for b in assistant_content if b.get("type") == "text"]
            combined = "\n".join(text_blocks).strip()
            if combined:
                return _wrap_finish(
                    {
                        "summary": combined,
                        "infrastructure_overview": combined,
                        "problem_framing": problem_statement,
                        "top_risks": [],
                        "recommended_chaos_focus": [],
                        "confidence": "low",
                        "data_gaps": ["Agent ended without calling finish_understanding"],
                    },
                    mode="llm",
                    iterations=iteration,
                    tool_trace=tool_trace,
                    problem_statement=problem_statement,
                    namespace=namespace,
                    target_label=target_label,
                )
            break

        tool_results: list[dict[str, Any]] = []
        for tu in tool_uses:
            name = tu["name"]
            tool_input = tu.get("input", {})
            tool_id = tu["id"]

            if name == "finish_understanding":
                tool_trace.append({"tool": name, "input": tool_input, "iteration": iteration})
                return _wrap_finish(
                    tool_input,
                    mode="llm",
                    iterations=iteration,
                    tool_trace=tool_trace,
                    problem_statement=problem_statement,
                    namespace=namespace,
                    target_label=target_label,
                )

            result = await registry.execute(name, tool_input)
            tool_trace.append(
                {
                    "tool": name,
                    "input": tool_input,
                    "iteration": iteration,
                    "result_preview": _preview(result),
                },
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": truncate_tool_result(result),
                },
            )

        messages.append({"role": "user", "content": tool_results})

    return await _rules_fallback(
        registry=registry,
        problem_statement=problem_statement,
        namespace=namespace,
        target_label=target_label,
        tool_trace=tool_trace,
        reason="max_iterations",
    )


def _build_initial_message(
    problem_statement: str,
    namespace: str,
    target_label: str,
    ctx: dict[str, Any] | None,
) -> str:
    parts = [
        f"Target: {target_label} (namespace={namespace})",
        f"Problem statement: {problem_statement or 'General resilience assessment — understand this environment.'}",
    ]
    if ctx:
        parts.append(
            f"Configured scope: cluster={ctx.get('cluster')}, aws_region={ctx.get('aws_region')}, "
            f"aws_account={ctx.get('aws_account')}, environment={ctx.get('environment')}",
        )
    parts.append("Use tools to read live and declared context, then call finish_understanding.")
    return "\n".join(parts)


def _preview(result: dict[str, Any]) -> str:
    text = json.dumps(result, default=str)
    return text[:400] + "…" if len(text) > 400 else text


def _wrap_finish(
    finish_payload: dict[str, Any],
    *,
    mode: str,
    iterations: int,
    tool_trace: list[dict[str, Any]],
    problem_statement: str,
    namespace: str,
    target_label: str,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "iterations": iterations,
        "problem_statement": problem_statement,
        "namespace": namespace,
        "target_label": target_label,
        "summary": finish_payload.get("summary", ""),
        "infrastructure_overview": finish_payload.get("infrastructure_overview", ""),
        "problem_framing": finish_payload.get("problem_framing", problem_statement),
        "top_risks": finish_payload.get("top_risks", []),
        "recommended_chaos_focus": finish_payload.get("recommended_chaos_focus", []),
        "confidence": finish_payload.get("confidence", "medium"),
        "data_gaps": finish_payload.get("data_gaps", []),
        "tool_trace": tool_trace,
    }


async def _rules_fallback(
    *,
    registry: ContextToolRegistry,
    problem_statement: str,
    namespace: str,
    target_label: str,
    tool_trace: list[dict[str, Any]] | None = None,
    reason: str = "llm_unavailable",
) -> dict[str, Any]:
    """Deterministic fallback: run all read tools once and synthesize a summary."""
    trace = list(tool_trace or [])
    snapshots: dict[str, Any] = {}

    for tool_name in (
        "get_live_snapshot",
        "probe_aws",
        "probe_target",
        "get_posture_gaps",
        "get_declared_context",
        "get_context_analysis",
        "get_integrations",
    ):
        result = await registry.execute(tool_name, {})
        snapshots[tool_name] = result
        trace.append({"tool": tool_name, "input": {}, "iteration": 0, "result_preview": _preview(result)})

    live = snapshots.get("get_live_snapshot", {})
    aws = snapshots.get("probe_aws", {})
    posture = snapshots.get("get_posture_gaps", {})
    declared = snapshots.get("get_declared_context", {})
    gaps = snapshots.get("get_context_analysis", {})

    apps = [a.get("name", "?") for a in live.get("applications", []) if isinstance(a, dict)]
    deps = [d.get("name", "?") for d in live.get("dependencies", []) if isinstance(d, dict)]
    rds = [r.get("id", "?") for r in aws.get("rds", []) if isinstance(r, dict)]
    posture_gap_count = len(posture.get("gaps", []))
    context_gap_count = len(gaps.get("gaps", [])) if gaps.get("found") else 0

    live_flag = live.get("live_data", False)
    aws_source = aws.get("source", "unknown")
    sources = live.get("collection_sources", {})

    overview_lines = [
        f"Applications: {', '.join(apps) or 'none'}",
        f"Dependencies: {', '.join(deps) or 'none'}",
        f"AWS RDS ({aws_source}): {', '.join(rds) or 'none'}",
        f"K8s source: {sources.get('kubernetes', 'unknown')}, AWS source: {sources.get('aws', 'unknown')}",
        f"Posture gaps: {posture_gap_count}, Context gaps: {context_gap_count}",
    ]

    data_gaps: list[str] = []
    if not live_flag:
        data_gaps.append("Infrastructure snapshot is not fully live — some rings use seed/catalog data")
    if aws_source != "live":
        data_gaps.append(f"AWS probe: {aws.get('fallback_reason') or 'using seed/fallback'}")
    if not declared.get("found"):
        data_gaps.append("No declared context (Terraform/README) ingested")

    top_risks = [g.get("message", "") for g in posture.get("gaps", [])[:5] if isinstance(g, dict)]
    if gaps.get("found"):
        top_risks.extend(g.get("message", "") for g in gaps.get("gaps", [])[:3] if isinstance(g, dict))

    return _wrap_finish(
        {
            "summary": (
                f"Rules-based context scan for {target_label}: {len(apps)} apps, {len(deps)} dependencies, "
                f"{posture_gap_count} posture gaps. "
                f"{'Live collectors reachable.' if live_flag and aws_source == 'live' else 'Partial seed/fallback data.'}"
            ),
            "infrastructure_overview": "\n".join(overview_lines),
            "problem_framing": problem_statement or "General environment assessment",
            "top_risks": top_risks[:8],
            "recommended_chaos_focus": _suggest_focus(posture.get("gaps", []), apps),
            "confidence": "high" if live_flag and aws_source == "live" else "medium" if live_flag or aws_source == "live" else "low",
            "data_gaps": data_gaps,
        },
        mode="rules",
        iterations=len([t for t in trace if t.get("iteration", 0) > 0]) or 1,
        tool_trace=trace,
        problem_statement=problem_statement,
        namespace=namespace,
        target_label=target_label,
    )


def _suggest_focus(gaps: list[dict[str, Any]], apps: list[str]) -> list[str]:
    focus: list[str] = []
    rules = {g.get("rule") for g in gaps if isinstance(g, dict)}
    if "critical-rds-multi-az" in rules:
        focus.append("RDS failover / single-AZ blast radius")
    if "critical-deployment-probes" in rules:
        focus.append("Missing readiness probes under load")
    if "critical-sqs-dlq" in rules:
        focus.append("SQS poison-message / DLQ absence")
    if "payments-api" in apps or "checkout" in apps:
        focus.append("Critical path dependency latency (payments/checkout)")
    if not focus:
        focus.append("Steady-state guard on primary service SLOs")
    return focus[:5]
