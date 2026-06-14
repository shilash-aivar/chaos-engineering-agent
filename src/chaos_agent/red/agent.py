"""Red agent v0 — plan resilience and optional security attacks from posture gaps."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from chaos_agent.security.catalog import RESILIENCE_ATTACKS, SECURITY_ATTACKS
from chaos_agent.security.types import AttackCategory, RedAttack, SecurityAttackSpec


def _spec_to_attack(spec: SecurityAttackSpec, round_num: int, rationale: str) -> RedAttack:
    faults: list[dict[str, str]] = []
    if spec.paired_fault:
        parts = spec.paired_fault.split(":", 1)
        faults.append({"type": parts[0], "target": parts[1] if len(parts) > 1 else spec.target_service})
    elif spec.category == AttackCategory.RESILIENCE:
        faults.append({"type": spec.technique, "target": spec.target_service})

    transcript = (
        f"Round {round_num}: {spec.name} on {spec.target_service}. "
        f"{rationale} Technique: {spec.technique}."
    )
    if spec.cwe:
        transcript += f" Maps to {spec.cwe}."
    if spec.cve_examples:
        transcript += f" CVE classes: {', '.join(spec.cve_examples[:3])}."
    if spec.category_name:
        transcript += f" [{spec.category_name}]"

    return RedAttack(
        id=f"atk-{uuid.uuid4().hex[:8]}",
        category=spec.category,
        title=spec.name,
        service=spec.target_service,
        technique=spec.technique,
        description=spec.description,
        cwe=spec.cwe,
        paired_fault=spec.paired_fault,
        transcript=transcript,
        faults=faults,
    )


def _gap_boosts_security(gap: dict[str, Any]) -> list[str]:
    """Map posture gaps to security techniques Red should prioritize."""
    rule = gap.get("rule", "")
    mapping = {
        "app-circuit-breaker": ["broken_auth_during_outage", "idor_under_latency"],
        "critical-deployment-probes": ["broken_auth_during_outage"],
        "deps-third-party-timeout": ["jwt_expired_token_probe", "error_path_secret_scan"],
        "critical-rds-multi-az": ["idor_under_latency", "dependency_blackhole"],
    }
    return mapping.get(rule, [])


def plan_attack(
    *,
    round_num: int,
    include_security: bool,
    security_mix_pct: int = 50,
    posture_gaps: list[dict[str, Any]],
    prior_techniques: list[str],
    attack_pool: Optional[list[SecurityAttackSpec]] = None,
) -> RedAttack:
    """Pick next attack. Uses framework-generated pool when provided."""
    boosted: list[str] = []
    for gap in posture_gaps:
        boosted.extend(_gap_boosts_security(gap))

    pool: list[SecurityAttackSpec] = list(RESILIENCE_ATTACKS)
    if attack_pool:
        pool = [s for s in attack_pool if s.technique not in prior_techniques]
        if not pool:
            pool = list(attack_pool)
        spec = pool[(round_num - 1) % len(pool)]
        rationale = f"Framework attack plan — {spec.category_name or spec.framework_id or 'custom'}."
        if spec.cve_examples:
            rationale += f" CVE classes: {', '.join(spec.cve_examples[:2])}."
        return _spec_to_attack(spec, round_num, rationale)

    if include_security:
        security_pool = [s for s in SECURITY_ATTACKS if s.technique not in prior_techniques]
        if not security_pool:
            security_pool = list(SECURITY_ATTACKS)
        hybrid = [s for s in security_pool if s.category == AttackCategory.HYBRID]
        pure_sec = [s for s in security_pool if s.category == AttackCategory.SECURITY]

        use_security = round_num > 1 or security_mix_pct >= 50
        if boosted and round_num >= 2:
            use_security = True

        if use_security and (round_num % 2 == 0 or security_mix_pct >= 70):
            pool = hybrid + pure_sec if hybrid else pure_sec
            rationale = "Posture weakness suggests security surface is exposed."
        elif use_security and security_mix_pct >= 30:
            pool = pure_sec + hybrid
            rationale = "User enabled security attacks for this campaign."
        else:
            pool = list(RESILIENCE_ATTACKS)
            rationale = "Resilience fault selected; security mix below threshold for this round."

        for technique in boosted:
            matched = [s for s in pool if s.technique == technique]
            if matched:
                spec = matched[0]
                return _spec_to_attack(
                    spec,
                    round_num,
                    f"Exploiting gap '{technique}' from posture scan. ",
                )
    else:
        rationale = "Security attacks disabled — resilience-only campaign."

    resilience_pool = [s for s in RESILIENCE_ATTACKS if s.technique not in prior_techniques]
    if not resilience_pool:
        resilience_pool = list(RESILIENCE_ATTACKS)
    spec = resilience_pool[(round_num - 1) % len(resilience_pool)]
    return _spec_to_attack(spec, round_num, rationale)
