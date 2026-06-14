"""Generate staging-safe attack specs from OWASP / MITRE / CWE frameworks."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from chaos_agent.security.catalog import RESILIENCE_ATTACKS
from chaos_agent.security.frameworks.registry import get_categories, get_framework
from chaos_agent.security.types import (
    AttackCategory,
    CweEntry,
    FrameworkCategory,
    GeneratedAttackPlan,
    SecurityAttackSpec,
)

# CWE prefix -> safe staging probe technique + default target
_PROBE_TEMPLATES: dict[str, dict[str, str]] = {
    "CWE-639": {"technique": "idor_enumeration_probe", "target": "checkout", "name": "IDOR / authorization bypass probe"},
    "CWE-863": {"technique": "idor_enumeration_probe", "target": "checkout", "name": "Incorrect authorization probe"},
    "CWE-862": {"technique": "idor_enumeration_probe", "target": "checkout", "name": "Missing authorization probe"},
    "CWE-22": {"technique": "path_traversal_probe", "target": "checkout", "name": "Path traversal probe"},
    "CWE-352": {"technique": "csrf_token_probe", "target": "checkout", "name": "CSRF protection probe"},
    "CWE-425": {"technique": "forced_browsing_probe", "target": "checkout", "name": "Forced browsing probe"},
    "CWE-319": {"technique": "cleartext_transport_probe", "target": "payments-api", "name": "Cleartext transport probe"},
    "CWE-798": {"technique": "hardcoded_secret_scan", "target": "payments-api", "name": "Hard-coded credential scan"},
    "CWE-326": {"technique": "weak_tls_probe", "target": "checkout", "name": "Weak TLS configuration probe"},
    "CWE-311": {"technique": "encryption_at_rest_probe", "target": "payments-db", "name": "Missing encryption probe"},
    "CWE-89": {"technique": "sqli_safe_probe", "target": "checkout", "name": "SQL injection safe probe"},
    "CWE-79": {"technique": "xss_reflected_probe", "target": "checkout", "name": "Reflected XSS probe"},
    "CWE-78": {"technique": "command_injection_safe_probe", "target": "checkout", "name": "Command injection safe probe"},
    "CWE-943": {"technique": "nosql_injection_safe_probe", "target": "checkout", "name": "NoSQL injection safe probe"},
    "CWE-840": {"technique": "business_logic_probe", "target": "checkout", "name": "Business logic flaw probe"},
    "CWE-16": {"technique": "security_misconfig_scan", "target": "payments-api", "name": "Security misconfiguration scan"},
    "CWE-209": {"technique": "error_path_secret_scan", "target": "payments-api", "name": "Error message leakage probe"},
    "CWE-200": {"technique": "sensitive_data_exposure_probe", "target": "payments-api", "name": "Sensitive data exposure probe"},
    "CWE-1104": {"technique": "vulnerable_component_scan", "target": "payments-api", "name": "Vulnerable dependency scan"},
    "CWE-287": {"technique": "jwt_expired_token_probe", "target": "payments-api", "name": "Authentication bypass probe"},
    "CWE-306": {"technique": "missing_auth_endpoint_probe", "target": "payments-api", "name": "Missing authentication probe"},
    "CWE-307": {"technique": "auth_rate_limit_flood", "target": "checkout", "name": "Auth brute-force probe"},
    "CWE-384": {"technique": "session_fixation_probe", "target": "checkout", "name": "Session fixation probe"},
    "CWE-494": {"technique": "unsigned_artifact_probe", "target": "payments-api", "name": "Unsigned update channel probe"},
    "CWE-502": {"technique": "deserialization_safe_probe", "target": "payments-api", "name": "Unsafe deserialization probe"},
    "CWE-918": {"technique": "ssrf_safe_probe", "target": "checkout", "name": "SSRF safe probe"},
    "CWE-778": {"technique": "insufficient_logging_probe", "target": "checkout", "name": "Insufficient logging probe"},
    "CWE-117": {"technique": "log_injection_probe", "target": "checkout", "name": "Log injection probe"},
}

_DEFAULT_PROBE = {
    "technique": "generic_security_probe",
    "target": "checkout",
    "name": "Generic security probe",
}

_HYBRID_CWES = {"CWE-639", "CWE-287", "CWE-306", "CWE-918", "CWE-307"}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _probe_for_cwe(
    cwe: CweEntry,
    category: FrameworkCategory,
    framework_id: str,
    namespace: str,
    target_services: dict[str, str],
) -> SecurityAttackSpec:
    template = _PROBE_TEMPLATES.get(cwe.id, _DEFAULT_PROBE)
    target = target_services.get(template["target"], template["target"])
    technique = template["technique"]
    is_hybrid = cwe.id in _HYBRID_CWES and framework_id == "owasp-top10-2021"

    paired_fault = None
    if is_hybrid:
        if cwe.id in ("CWE-287", "CWE-306"):
            paired_fault = "pod_kill:auth-service"
        elif cwe.id == "CWE-639":
            paired_fault = "dependency_blackhole:payments-db"
        elif cwe.id == "CWE-918":
            paired_fault = "network_latency:inventory-api"

    cve_str = ", ".join(cwe.example_cves[:3]) if cwe.example_cves else "none"
    description = (
        f"Staging-safe probe for {cwe.id} ({cwe.name}) under {category.name}. "
        f"Representative CVE classes: {cve_str}. Namespace: {namespace}."
    )

    severity = "critical" if cwe.id in ("CWE-89", "CWE-639", "CWE-918", "CWE-287", "CWE-502") else "high"

    return SecurityAttackSpec(
        id=f"gen-{_slug(framework_id)}-{_slug(category.id)}-{_slug(cwe.id)}",
        name=f"{template['name']} — {cwe.name}",
        category=AttackCategory.HYBRID if paired_fault else AttackCategory.SECURITY,
        technique=technique,
        target_service=target,
        description=description,
        cwe=cwe.id,
        cwe_ids=[cwe.id],
        cve_examples=list(cwe.example_cves),
        paired_fault=paired_fault,
        severity_if_success=severity,
        framework_id=framework_id,
        category_id=category.id,
        category_name=category.name,
        mitre_technique_id=category.mitre_techniques[0] if category.mitre_techniques else None,
        owasp_rank=category.id if framework_id == "owasp-top10-2021" else None,
    )


def _resilience_from_framework(
    framework_id: str,
    categories: list[FrameworkCategory],
    namespace: str,
) -> list[SecurityAttackSpec]:
    if framework_id != "resilience-chaos":
        return []
    attacks: list[SecurityAttackSpec] = []
    for cat in categories:
        for res in RESILIENCE_ATTACKS:
            attacks.append(
                res.model_copy(
                    update={
                        "framework_id": framework_id,
                        "category_id": cat.id,
                        "category_name": cat.name,
                        "description": f"{res.description} ({cat.name}, {namespace})",
                    },
                ),
            )
    return attacks


def generate_attack_plan(
    *,
    framework_id: str,
    namespace: str = "staging",
    category_ids: Optional[List[str]] = None,
    target_services: Optional[Dict[str, str]] = None,
) -> GeneratedAttackPlan:
    """Build one probe per CWE in selected framework categories."""
    fw = get_framework(framework_id)
    if fw is None:
        raise ValueError(f"Unknown framework: {framework_id}")

    categories = get_categories(framework_id, category_ids)
    targets = target_services or {}

    if framework_id == "resilience-chaos":
        attacks = _resilience_from_framework(framework_id, categories, namespace)
        return GeneratedAttackPlan(
            framework_id=framework_id,
            framework_name=fw.name,
            namespace=namespace,
            category_ids=[c.id for c in categories],
            attacks=attacks,
            total_cwes=0,
            total_cve_examples=0,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    attacks: list[SecurityAttackSpec] = []
    cwe_count = 0
    cve_count = 0

    for category in categories:
        for cwe in category.cwes:
            cwe_count += 1
            cve_count += len(cwe.example_cves)
            attacks.append(_probe_for_cwe(cwe, category, framework_id, namespace, targets))

    return GeneratedAttackPlan(
        framework_id=framework_id,
        framework_name=fw.name,
        namespace=namespace,
        category_ids=[c.id for c in categories],
        attacks=attacks,
        total_cwes=cwe_count,
        total_cve_examples=cve_count,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
