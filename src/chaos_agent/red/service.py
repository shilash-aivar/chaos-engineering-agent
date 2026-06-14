"""Red agent service — unified attack planning."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.posture.scanner import PostureScanner
from chaos_agent.red.agent import plan_attack
from chaos_agent.red.llm import enhance_red_attack, plan_attack_llm
from chaos_agent.red_blue.experiments import inject_attack
from chaos_agent.security.types import RedAttack, SecurityAttackSpec


async def plan_red_attack(
    *,
    round_num: int = 1,
    namespace: str = "staging",
    include_security: bool = False,
    security_mix_pct: int = 50,
    prior_techniques: Optional[list[str]] = None,
    posture_gaps: Optional[list[dict[str, Any]]] = None,
    attack_pool: Optional[list[SecurityAttackSpec]] = None,
    use_llm: bool = True,
) -> RedAttack:
    scanner = PostureScanner(namespace)
    gaps = posture_gaps if posture_gaps is not None else (await scanner.scan()).get("gaps", [])
    prior = prior_techniques or []

    if use_llm and not attack_pool:
        llm_attack = await plan_attack_llm(
            round_num=round_num,
            posture_gaps=gaps,
            prior_techniques=prior,
            include_security=include_security,
        )
        if llm_attack is not None:
            return await enhance_red_attack(llm_attack, posture_gaps=gaps, round_num=round_num)

    attack = plan_attack(
        round_num=round_num,
        include_security=include_security,
        security_mix_pct=security_mix_pct,
        posture_gaps=gaps,
        prior_techniques=prior,
        attack_pool=attack_pool,
    )
    return await enhance_red_attack(attack, posture_gaps=gaps, round_num=round_num)


async def execute_red_attack(attack: RedAttack, namespace: str = "staging") -> dict[str, Any]:
    return await inject_attack(attack, namespace)
