"""LLM full attack planning for Red agent."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from chaos_agent.composer.prompts import RED_PLAN_SYSTEM
from chaos_agent.config import get_settings
from chaos_agent.llm.client import get_llm_client
from chaos_agent.red.agent import plan_attack
from chaos_agent.security.types import AttackCategory, RedAttack


async def plan_attack_llm(
    *,
    round_num: int,
    posture_gaps: list[dict[str, Any]],
    prior_techniques: list[str],
    include_security: bool = False,
) -> Optional[RedAttack]:
    settings = get_settings()
    if not settings.llm_enabled:
        return None
    llm = get_llm_client()
    if not llm.available:
        return None

    fallback = plan_attack(
        round_num=round_num,
        include_security=include_security,
        posture_gaps=posture_gaps,
        prior_techniques=prior_techniques,
    )
    payload = {
        "round": round_num,
        "posture_gaps": posture_gaps[:10],
        "prior_techniques": prior_techniques,
        "include_security": include_security,
        "fallback_attack": fallback.model_dump(),
    }
    data = await llm.complete_json(system=RED_PLAN_SYSTEM, user=json.dumps(payload, indent=2))
    if not data:
        return None

    try:
        cat = AttackCategory(str(data.get("category", fallback.category.value)))
    except ValueError:
        cat = fallback.category

    faults = data.get("faults") or fallback.faults
    transcript_parts = data.get("transcript") or [str(data.get("rationale", fallback.transcript))]
    return RedAttack(
        id=f"atk-{uuid.uuid4().hex[:8]}",
        category=cat,
        title=str(data.get("title", fallback.title)),
        service=str(data.get("service", fallback.service)),
        technique=str(data.get("technique", fallback.technique)),
        description=str(data.get("description", fallback.description)),
        cwe=fallback.cwe,
        paired_fault=fallback.paired_fault,
        transcript=" ".join(str(t) for t in transcript_parts[:3]),
        faults=[{"type": str(f.get("type")), "target": str(f.get("target"))} for f in faults],
    )


async def enhance_red_attack(
    attack: RedAttack,
    *,
    posture_gaps: list[dict[str, Any]],
    round_num: int,
) -> RedAttack:
    from chaos_agent.composer.prompts import RED_SYSTEM

    llm = get_llm_client()
    if not llm.available:
        return attack

    payload = {
        "round": round_num,
        "attack": attack.model_dump(),
        "posture_gaps": posture_gaps[:8],
    }
    data = await llm.complete_json(system=RED_SYSTEM, user=json.dumps(payload, indent=2))
    if not data:
        return attack

    transcript_lines = data.get("transcript") or []
    rationale = data.get("rationale")
    if transcript_lines:
        attack.transcript = " ".join(str(t) for t in transcript_lines[:3])
    elif rationale:
        attack.transcript = f"{attack.transcript} {rationale}"
    return attack
