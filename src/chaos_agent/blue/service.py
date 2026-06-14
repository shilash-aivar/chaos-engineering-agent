"""Blue agent service — suggestions, defense, verify."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.blue.agent import defend_attack, suggest_fixes
from chaos_agent.blue.llm import enhance_blue_defense, suggest_fixes_llm
from chaos_agent.blue.remediation import open_blue_pr, verify_round_full
from chaos_agent.context.types import BlueSuggestion, ContextGap
from chaos_agent.posture.scanner import PostureScanner
from chaos_agent.security.types import BlueDefense, RedAttack


async def get_blue_suggestions(
    gaps: list[ContextGap],
    *,
    use_llm: bool = True,
) -> list[BlueSuggestion]:
    if use_llm:
        llm_suggestions = await suggest_fixes_llm(gaps)
        if llm_suggestions:
            return llm_suggestions
    return suggest_fixes(gaps)


async def defend_red_attack(
    attack: RedAttack,
    *,
    posture_gaps: Optional[list[dict[str, Any]]] = None,
    evidence_summary: Optional[list[str]] = None,
    namespace: str = "staging",
    use_llm: bool = True,
) -> BlueDefense:
    if posture_gaps is None:
        scanner = PostureScanner(namespace)
        posture_gaps = (await scanner.scan()).get("gaps", [])

    defense = defend_attack(attack)
    if use_llm:
        defense = await enhance_blue_defense(
            defense,
            attack,
            posture_gaps=posture_gaps,
            evidence_summary=evidence_summary,
        )
    return defense


async def remediate_defense(defense: BlueDefense) -> dict[str, Any]:
    return await open_blue_pr(defense)


async def verify_defense(
    attack: RedAttack,
    defense: BlueDefense,
    *,
    namespace: str = "staging",
    re_inject: bool = True,
) -> dict[str, Any]:
    return await verify_round_full(
        attack,
        defense,
        namespace=namespace,
        re_inject=re_inject,
    )
