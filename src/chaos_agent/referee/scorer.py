"""Referee — deterministic round scoring for Red vs Blue."""

from __future__ import annotations

from typing import Any, Optional

from chaos_agent.security.types import AttackCategory, BlueDefense, RedAttack, RoundResult


def _attack_succeeds(attack: RedAttack, posture_gaps: list[dict[str, Any]]) -> bool:
    """Heuristic: attack succeeds when posture lacks expected controls."""
    gap_rules = {g.get("rule") for g in posture_gaps}
    gap_services = {g.get("service") for g in posture_gaps}

    security_success_map = {
        "jwt_expired_token_probe": "deps-third-party-timeout" in gap_rules,
        "idor_enumeration_probe": attack.service in gap_services,
        "auth_rate_limit_flood": "app-circuit-breaker" in gap_rules,
        "session_cookie_flags_audit": True,
        "broken_auth_during_outage": "critical-deployment-probes" in gap_rules,
        "error_path_secret_scan": "deps-third-party-timeout" in gap_rules,
        "idor_under_latency": "critical-rds-multi-az" in gap_rules,
    }
    resilience_success_map = {
        "dependency_blackhole": "critical-rds-multi-az" in gap_rules or attack.service in gap_services,
        "pod_kill": "critical-pods-priority-class" in gap_rules,
        "network_latency": "app-circuit-breaker" in gap_rules,
    }

    if attack.category in (AttackCategory.SECURITY, AttackCategory.HYBRID):
        return security_success_map.get(attack.technique, True)
    return resilience_success_map.get(attack.technique, True)


def _defense_effective(attack: RedAttack, defense: BlueDefense) -> bool:
    technique = attack.technique
    diff_lower = defense.suggested_diff.lower()
    title_lower = defense.title.lower()

    checks = {
        "jwt_expired_token_probe": "exp" in diff_lower or "jwt" in title_lower,
        "idor_enumeration_probe": "authorize" in diff_lower or "idor" in title_lower or "ownership" in diff_lower,
        "auth_rate_limit_flood": "rate" in diff_lower or "throttle" in title_lower,
        "session_cookie_flags_audit": "httponly" in diff_lower or "samesite" in diff_lower,
        "broken_auth_during_outage": "fail" in diff_lower or "401" in diff_lower or "unauthorized" in diff_lower,
        "error_path_secret_scan": "sanitize" in diff_lower or "error" in title_lower,
        "idor_under_latency": "multi_az" in diff_lower or "transaction" in diff_lower,
        "dependency_blackhole": "multi_az" in diff_lower or "pool" in diff_lower,
        "pod_kill": "priority" in diff_lower or "probe" in diff_lower,
        "network_latency": "retry" in diff_lower or "circuit" in diff_lower,
    }
    return checks.get(technique, len(defense.suggested_diff) > 20)


def score_round(
    *,
    round_num: int,
    attack: RedAttack,
    defense: BlueDefense,
    posture_gaps: list[dict[str, Any]],
    inject_result: Optional[dict[str, Any]] = None,
) -> RoundResult:
    red_success = _attack_succeeds(attack, posture_gaps)
    blue_effective = _defense_effective(attack, defense)

    slo_breached = bool(inject_result and inject_result.get("slo_breached"))
    injected = bool(inject_result and inject_result.get("injected"))
    if inject_result:
        red_success = slo_breached or injected
        if not slo_breached and injected:
            blue_effective = True

    # Weighted breakdown aligned with /platform/scoring
    attack_weight = 25
    defense_weight = 25
    detection_weight = 15
    recovery_weight = 20
    remediation_weight = 15

    red_breakdown = {
        "attack_success": attack_weight if red_success else attack_weight // 3,
        "detection_delay": detection_weight // 2 if red_success else 0,
    }
    blue_breakdown = {
        "defense_effective": defense_weight if blue_effective else defense_weight // 3,
        "recovery": recovery_weight if not slo_breached else recovery_weight // 4,
        "remediation": remediation_weight if blue_effective else 0,
    }

    red_points = sum(red_breakdown.values()) + (10 if attack.category == AttackCategory.HYBRID else 0)
    blue_points = sum(blue_breakdown.values())
    if blue_effective and red_success:
        blue_points += 10

    if red_points > blue_points + 5:
        outcome = "red_win"
        referee_note = (
            f"Round {round_num}: Red {red_points} · Blue {blue_points}. "
            f"Attack '{attack.title}' breached defenses."
        )
    elif blue_points > red_points + 5:
        outcome = "blue_win"
        referee_note = (
            f"Round {round_num}: Red {red_points} · Blue {blue_points}. "
            f"Blue countered with '{defense.title}'."
        )
    else:
        outcome = "draw"
        referee_note = (
            f"Round {round_num}: Red {red_points} · Blue {blue_points}. "
            "Equilibrium — export to regression suite."
        )

    referee_note += f" | slo_breached={slo_breached}"

    red_transcript = [
        attack.transcript,
        f"Executed {attack.technique} against {attack.service}.",
        f"{'Breach confirmed' if red_success else 'Partial impact'} — score +{red_points}.",
    ]
    blue_transcript = [
        defense.transcript,
        f"Countermeasure: {defense.action}",
        f"{'Defense effective' if blue_effective else 'Mitigation drafted'} — score +{blue_points}.",
    ]

    if inject_result:
        red_transcript.append(
            f"Orchestrator experiment {inject_result.get('experiment_id')}: "
            f"state={inject_result.get('state')} slo_breached={slo_breached}"
        )

    return RoundResult(
        round=round_num,
        attack=attack,
        defense=defense,
        red_points=red_points,
        blue_points=blue_points,
        outcome=outcome,
        referee_note=referee_note,
        red_transcript=red_transcript,
        blue_transcript=blue_transcript,
    )
