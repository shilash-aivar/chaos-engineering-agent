"""Compare declared context vs live snapshot vs posture — produce level-tagged gaps."""

from __future__ import annotations

from chaos_agent.context.types import ContextGap, ContextSnapshot, DeclaredContext, PracticeLevel
from chaos_agent.graph.types import InfraSnapshot
from chaos_agent.posture.scanner import PostureScanner


async def analyze_context(
    context: ContextSnapshot,
    namespace: str = "staging",
) -> tuple[list[ContextGap], dict[str, int]]:
    scanner = PostureScanner(namespace)
    posture = await scanner.scan()
    snapshot = await scanner.builder.build()

    gaps: list[ContextGap] = []
    gap_id = 0

    for pg in posture["gaps"]:
        gap_id += 1
        level = _scope_to_level(pg["rule"], pg["scope"])
        gaps.append(
            ContextGap(
                id=f"ctx-{gap_id:03d}",
                level=level,
                scope=pg["scope"],
                severity=pg["severity"],
                service=pg["service"],
                rule=pg["rule"],
                message=pg["message"],
                observed_evidence=[pg["message"]],
                declared_evidence=_declared_for_rule(context.declared, pg["rule"], snapshot),
                policy_rule=pg["rule"],
            ),
        )

    gaps.extend(_declared_vs_observed_gaps(context.declared, snapshot, gap_id))
    return gaps, posture.get("summary", {})


def sast_findings_to_gaps(findings: list[dict], start_id: int) -> list[ContextGap]:
    gaps: list[ContextGap] = []
    gid = start_id
    for f in findings:
        gid += 1
        gaps.append(
            ContextGap(
                id=f"ctx-{gid:03d}",
                level=PracticeLevel.SECURITY,
                scope="app",
                severity=f.get("severity", "medium"),
                service=f.get("file_path", "app").split("/")[0],
                rule=f"sast-{f.get('rule_id', 'finding')}",
                message=f.get("message", "SAST finding"),
                observed_evidence=[
                    f"{f.get('scanner')}: {f.get('file_path')}"
                    + (f":{f.get('line')}" if f.get("line") else ""),
                ],
                declared_evidence=[f.get("cwe", "CWE-unknown")],
                policy_rule=f.get("rule_id"),
            ),
        )
    return gaps


def _scope_to_level(rule: str, scope: str) -> PracticeLevel:
    mapping = {
        "critical-rds-multi-az": PracticeLevel.DB,
        "critical-sqs-dlq": PracticeLevel.HA,
        "critical-pods-priority-class": PracticeLevel.INFRA,
        "critical-deployment-probes": PracticeLevel.RELIABILITY,
        "critical-deployment-pdb": PracticeLevel.HA,
        "app-circuit-breaker": PracticeLevel.APP,
        "deps-db-pool-size": PracticeLevel.DB,
        "deps-third-party-timeout": PracticeLevel.DEPENDENCY,
        "obs-prometheus-scrape": PracticeLevel.MONITORING,
        "obs-trace-coverage": PracticeLevel.MONITORING,
        "alb-health-check": PracticeLevel.INFRA,
    }
    if rule in mapping:
        return mapping[rule]
    scope_map = {
        "k8s": PracticeLevel.INFRA,
        "aws": PracticeLevel.INFRA,
        "app": PracticeLevel.APP,
        "deps": PracticeLevel.DEPENDENCY,
        "observability": PracticeLevel.MONITORING,
    }
    return scope_map.get(scope, PracticeLevel.RESILIENCY)


def _declared_for_rule(declared: DeclaredContext, rule: str, snapshot: InfraSnapshot) -> list[str]:
    evidence: list[str] = []
    for doc in declared.documents:
        for claim in doc.claims:
            if rule == "critical-rds-multi-az" and "multi" in claim.lower():
                evidence.append(f"{doc.name}: {claim}")
            if rule == "app-circuit-breaker" and "circuit" in claim.lower():
                evidence.append(f"{doc.name}: {claim}")

    for res in declared.terraform_resources:
        if res.type == "aws_db_instance":
            multi = res.attributes.get("multi_az", res.attributes.get("multi_az", False))
            evidence.append(
                f"Terraform {res.name}: multi_az={multi} ({res.source_file})",
            )
        if res.type == "aws_sqs_queue" and "redrive" not in str(res.attributes):
            evidence.append(f"Terraform {res.name}: no redrive_policy ({res.source_file})")

    for hint in declared.code_hints:
        if "pool" in hint.lower() and "deps-db" in rule:
            evidence.append(hint)
        if "timeout" in hint.lower() and "third-party" in rule:
            evidence.append(hint)

    if not evidence:
        evidence.append("No matching declared artifact for this rule")
    return evidence


def _declared_vs_observed_gaps(
    declared: DeclaredContext,
    snapshot: InfraSnapshot,
    start_id: int,
) -> list[ContextGap]:
    extra: list[ContextGap] = []
    gid = start_id

    ha_claims = any("high availability" in c.lower() or "multi-az" in c.lower() for d in declared.documents for c in d.claims)
    rds_multi = any(
        r.type == "aws_db_instance" and r.attributes.get("multi_az") is True
        for r in declared.terraform_resources
    )
    live_single_az = any(
        r.get("id") == "payments-db" and not r.get("multi_az")
        for r in snapshot.aws.get("rds", [])
    )
    if ha_claims and live_single_az and not rds_multi:
        gid += 1
        extra.append(
            ContextGap(
                id=f"ctx-{gid:03d}",
                level=PracticeLevel.HA,
                scope="aws",
                severity="critical",
                service="payments-db",
                rule="declared-ha-mismatch",
                message="Docs claim HA but Terraform/live RDS is single-AZ",
                declared_evidence=[c for d in declared.documents for c in d.claims if "ha" in c.lower() or "multi" in c.lower()],
                observed_evidence=["Live snapshot: payments-db multi_az=false"],
            ),
        )

    slo_claims = any("slo" in c.lower() or "error budget" in c.lower() for d in declared.documents for c in d.claims)
    prom_ok = any(o.name == "prometheus" and o.status == "ok" for o in snapshot.observability)
    if slo_claims and not prom_ok:
        gid += 1
        extra.append(
            ContextGap(
                id=f"ctx-{gid:03d}",
                level=PracticeLevel.MONITORING,
                scope="observability",
                severity="high",
                service="prometheus",
                rule="declared-observability-gap",
                message="README defines SLOs but Prometheus target is not healthy",
                declared_evidence=[c for d in declared.documents for c in d.claims if "slo" in c.lower()],
                observed_evidence=["Observability ring: prometheus not ok"],
            ),
        )

    return extra
