"""LLM enhancements for Blue agent."""

from __future__ import annotations

import json
from typing import Any, Optional

from chaos_agent.blue.agent import defend_attack, suggest_fixes
from chaos_agent.composer.prompts import BLUE_SUGGEST_SYSTEM, BLUE_SYSTEM
from chaos_agent.config import get_settings
from chaos_agent.context.types import BlueSuggestion, ContextGap, PracticeLevel
from chaos_agent.llm.client import get_llm_client
from chaos_agent.security.types import BlueDefense, RedAttack


async def suggest_fixes_llm(gaps: list[ContextGap]) -> list[BlueSuggestion]:
    settings = get_settings()
    if not settings.llm_enabled:
        return []
    llm = get_llm_client()
    if not llm.available:
        return []

    payload = {
        "gaps": [g.model_dump() for g in gaps[:12]],
        "rule_fallback": [s.model_dump() for s in suggest_fixes(gaps)[:6]],
    }
    data = await llm.complete_json(system=BLUE_SUGGEST_SYSTEM, user=json.dumps(payload, indent=2))
    if not data or "suggestions" not in data:
        return []

    out: list[BlueSuggestion] = []
    for raw in data["suggestions"][:12]:
        try:
            level = PracticeLevel(str(raw.get("level", "app")))
        except ValueError:
            level = PracticeLevel.APP
        out.append(
            BlueSuggestion(
                finding_id=str(raw.get("finding_id", "gap")),
                level=level,
                title=str(raw.get("title", "Fix")),
                action=str(raw.get("action", "")),
                artifact_type=str(raw.get("artifact_type", "runbook")),
                target_path=str(raw.get("target_path", "")),
                suggested_diff=str(raw.get("suggested_diff", "")),
                requires_approval=bool(raw.get("requires_approval", True)),
            ),
        )
    return out


async def enhance_blue_defense(
    defense: BlueDefense,
    attack: RedAttack,
    *,
    posture_gaps: list[dict[str, Any]],
    evidence_summary: Optional[list[str]] = None,
) -> BlueDefense:
    settings = get_settings()
    if not settings.llm_enabled:
        return defense
    llm = get_llm_client()
    if not llm.available:
        return defense

    payload = {
        "attack": attack.model_dump(),
        "defense_draft": defense.model_dump(),
        "posture_gaps": posture_gaps[:8],
        "evidence": evidence_summary or [],
    }
    data = await llm.complete_json(system=BLUE_SYSTEM, user=json.dumps(payload, indent=2))
    if not data:
        return defense

    defense.title = str(data.get("title") or defense.title)
    defense.action = str(data.get("action") or defense.action)
    defense.target_path = str(data.get("target_path") or defense.target_path)
    defense.artifact_type = str(data.get("artifact_type") or defense.artifact_type)
    defense.suggested_diff = str(data.get("suggested_diff") or defense.suggested_diff)
    transcript = data.get("transcript")
    if transcript:
        defense.transcript = " ".join(str(t) for t in transcript[:3])
    return defense
