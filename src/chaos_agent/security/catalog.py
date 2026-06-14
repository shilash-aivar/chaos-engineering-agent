"""Catalog of safe staging security probes Red can run (simulated DAST-style)."""

from __future__ import annotations

from typing import Optional

from chaos_agent.security.types import AttackCategory, SecurityAttackSpec

SECURITY_ATTACKS: list[SecurityAttackSpec] = [
    SecurityAttackSpec(
        id="sec-jwt-expiry",
        name="Expired JWT acceptance",
        category=AttackCategory.SECURITY,
        technique="jwt_expired_token_probe",
        target_service="payments-api",
        description="Replay tokens past exp claim against protected endpoints",
        cwe="CWE-287",
        severity_if_success="critical",
    ),
    SecurityAttackSpec(
        id="sec-idor-orders",
        name="IDOR order enumeration",
        category=AttackCategory.SECURITY,
        technique="idor_enumeration_probe",
        target_service="checkout",
        description="Sequential order ID probe across session boundaries",
        cwe="CWE-639",
        severity_if_success="critical",
    ),
    SecurityAttackSpec(
        id="sec-rate-limit-auth",
        name="Auth endpoint rate-limit bypass",
        category=AttackCategory.SECURITY,
        technique="auth_rate_limit_flood",
        target_service="checkout",
        description="Burst login attempts to detect missing throttling",
        cwe="CWE-307",
        severity_if_success="high",
    ),
    SecurityAttackSpec(
        id="sec-session-cookies",
        name="Session cookie hardening audit",
        category=AttackCategory.SECURITY,
        technique="session_cookie_flags_audit",
        target_service="checkout",
        description="Check Secure, HttpOnly, SameSite on session cookies",
        cwe="CWE-614",
        severity_if_success="medium",
    ),
    SecurityAttackSpec(
        id="sec-broken-auth-outage",
        name="Broken auth during dependency outage",
        category=AttackCategory.HYBRID,
        technique="broken_auth_during_outage",
        target_service="checkout",
        description="Kill auth dependency mid-session — app must fail closed",
        cwe="CWE-306",
        paired_fault="pod_kill:auth-service",
        severity_if_success="critical",
    ),
    SecurityAttackSpec(
        id="sec-secret-leak-errors",
        name="Secret leakage in error responses",
        category=AttackCategory.SECURITY,
        technique="error_path_secret_scan",
        target_service="payments-api",
        description="Trigger validation errors and scan bodies for tokens/keys",
        cwe="CWE-209",
        severity_if_success="high",
    ),
    SecurityAttackSpec(
        id="sec-hybrid-db-idor",
        name="IDOR under DB latency",
        category=AttackCategory.HYBRID,
        technique="idor_under_latency",
        target_service="checkout",
        description="Enumerate resources while DB blackholed — race on auth checks",
        cwe="CWE-639",
        paired_fault="dependency_blackhole:payments-db",
        severity_if_success="critical",
    ),
]

RESILIENCE_ATTACKS: list[SecurityAttackSpec] = [
    SecurityAttackSpec(
        id="res-db-blackhole-load",
        name="DB blackhole during load",
        category=AttackCategory.RESILIENCE,
        technique="dependency_blackhole",
        target_service="payments-db",
        description="Toxiproxy TCP blackhole on payments-db during k6 load on checkout",
        paired_fault="dependency_blackhole:payments-db",
        severity_if_success="critical",
    ),
    SecurityAttackSpec(
        id="res-pod-kill-critical",
        name="Critical pod kill",
        category=AttackCategory.RESILIENCE,
        technique="pod_kill",
        target_service="payments-api",
        description="Random pod termination on tier=critical deployment",
        paired_fault="pod_kill:payments-api",
        severity_if_success="high",
    ),
    SecurityAttackSpec(
        id="res-inventory-latency",
        name="Upstream latency cascade",
        category=AttackCategory.RESILIENCE,
        technique="network_latency",
        target_service="inventory-api",
        description="500ms latency on inventory during checkout traffic",
        paired_fault="network_latency:inventory-api",
        severity_if_success="high",
    ),
]


def list_security_attacks() -> list[SecurityAttackSpec]:
    return list(SECURITY_ATTACKS)


def list_all_attacks() -> list[SecurityAttackSpec]:
    return SECURITY_ATTACKS + RESILIENCE_ATTACKS


def get_attack(attack_id: str) -> Optional[SecurityAttackSpec]:
    for spec in list_all_attacks():
        if spec.id == attack_id:
            return spec
    return None
