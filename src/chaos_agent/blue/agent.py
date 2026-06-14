"""Blue agent v0 — rule-based prescriptions with artifact diffs from context gaps."""

from __future__ import annotations

from typing import Optional

from chaos_agent.context.types import BlueSuggestion, ContextGap, PracticeLevel


def suggest_fixes(gaps: list[ContextGap]) -> list[BlueSuggestion]:
    suggestions: list[BlueSuggestion] = []
    for gap in gaps:
        s = _suggest_for_gap(gap)
        if s:
            suggestions.append(s)
    return suggestions


def _suggest_for_gap(gap: ContextGap) -> Optional[BlueSuggestion]:
    rule = gap.rule
    if rule == "critical-rds-multi-az":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.DB,
            title="Enable RDS Multi-AZ",
            action="Update Terraform to set multi_az = true on payments-db",
            artifact_type="terraform",
            target_path="infra/rds.tf",
            suggested_diff=_rds_multi_az_diff(),
        )
    if rule == "critical-sqs-dlq":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.HA,
            title="Add SQS dead-letter queue",
            action="Configure redrive_policy on order-events queue",
            artifact_type="terraform",
            target_path="infra/sqs.tf",
            suggested_diff=_sqs_dlq_diff(),
        )
    if rule == "critical-pods-priority-class":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.INFRA,
            title="Add PriorityClass for critical pods",
            action="Create chaos-critical PriorityClass and patch deployment",
            artifact_type="manifest",
            target_path=f"k8s/{gap.service}-deployment.yaml",
            suggested_diff=_priority_class_diff(gap.service),
        )
    if rule == "critical-deployment-probes":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.RELIABILITY,
            title="Add readiness and liveness probes",
            action=f"Patch {gap.service} Deployment with httpGet /health probes",
            artifact_type="manifest",
            target_path=f"k8s/{gap.service}-deployment.yaml",
            suggested_diff=_probes_diff(gap.service),
        )
    if rule == "app-circuit-breaker":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.APP,
            title="Add circuit breaker on outbound calls",
            action="Istio VirtualService retry + outlier detection or app-level CB",
            artifact_type="config",
            target_path=f"mesh/{gap.service}-vs.yaml",
            suggested_diff=_istio_retry_diff(gap.service),
        )
    if rule == "deps-third-party-timeout":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.DEPENDENCY,
            title="Set client timeout on third-party dependency",
            action="Add 5s timeout with bounded retry on HTTP client",
            artifact_type="code",
            target_path=f"src/{gap.service}/client.py",
            suggested_diff=_client_timeout_diff(),
        )
    if rule == "deps-db-pool-size":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.DB,
            title="Increase database connection pool",
            action="Raise pool_size and add connection timeout",
            artifact_type="code",
            target_path="src/config/database.py",
            suggested_diff=_pool_size_diff(),
        )
    if rule == "declared-observability-gap":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.MONITORING,
            title="Align monitoring with documented claims",
            action="Add Prometheus scrape or OTel spans for claimed SLO path",
            artifact_type="config",
            target_path="observability/prometheus-scrape.yaml",
            suggested_diff="# Add ServiceMonitor for critical path\n# See README claims — wire metrics named in docs",
        )
    if rule == "declared-ha-mismatch":
        return BlueSuggestion(
            finding_id=gap.id,
            level=PracticeLevel.HA,
            title="Close HA documentation vs infrastructure gap",
            action="Either update docs or apply HA controls in Terraform/K8s",
            artifact_type="runbook",
            target_path="docs/HA.md",
            suggested_diff="# Reconcile: README claims HA but live/TF does not show Multi-AZ or PDB",
        )
    return BlueSuggestion(
        finding_id=gap.id,
        level=gap.level,
        title=gap.message[:80],
        action=gap.message,
        artifact_type="runbook",
        target_path="docs/resilience-runbook.md",
        suggested_diff=f"# Remediation for {gap.rule}\n# Service: {gap.service}\n# Review declared vs observed evidence",
    )


def _pool_size_diff() -> str:
    return """# database pool
POOL_SIZE = 25  # was: 10
POOL_TIMEOUT_SECONDS = 3"""


def defend_attack(attack: "RedAttack") -> "BlueDefense":
    """Blue counter for a Red attack — resilience or security."""
    from chaos_agent.security.types import AttackCategory, BlueDefense, RedAttack

    technique = attack.technique
    if technique == "jwt_expired_token_probe":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.SECURITY,
            title="Harden JWT validation",
            action="Reject expired tokens; validate exp, iss, aud on every request",
            artifact_type="code",
            target_path=f"src/{attack.service}/auth.py",
            suggested_diff=_jwt_hardening_diff(),
            transcript=f"Detected weak JWT checks on {attack.service}. Drafting auth middleware patch.",
        )
    if technique == "idor_enumeration_probe":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.SECURITY,
            title="Add object-level authorization",
            action="Verify resource ownership before returning order details",
            artifact_type="code",
            target_path=f"src/{attack.service}/orders.py",
            suggested_diff=_idor_guard_diff(),
            transcript=f"IDOR probe hit {attack.service}. Adding ownership check on GET /orders/:id.",
        )
    if technique == "auth_rate_limit_flood":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.SECURITY,
            title="Rate-limit authentication",
            action="Add per-IP and per-account throttling on /login",
            artifact_type="config",
            target_path=f"mesh/{attack.service}-rate-limit.yaml",
            suggested_diff=_rate_limit_diff(attack.service),
            transcript=f"Auth flood against {attack.service}. Deploying Envoy local rate limit.",
        )
    if technique == "session_cookie_flags_audit":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.SECURITY,
            title="Fix session cookie flags",
            action="Set Secure, HttpOnly, SameSite=Strict on session cookie",
            artifact_type="code",
            target_path=f"src/{attack.service}/session.py",
            suggested_diff=_session_cookie_diff(),
            transcript=f"Session cookies on {attack.service} missing hardening flags.",
        )
    if technique == "broken_auth_during_outage":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.HYBRID,
            title="Fail closed when auth dependency unavailable",
            action="Return 401 on auth service timeout; never serve cached identity",
            artifact_type="code",
            target_path=f"src/{attack.service}/middleware/auth.py",
            suggested_diff=_fail_closed_auth_diff(),
            transcript=f"Auth dependency killed during session on {attack.service}. Enforcing fail-closed.",
        )
    if technique == "error_path_secret_scan":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.SECURITY,
            title="Sanitize error responses",
            action="Strip stack traces and secrets from 4xx/5xx JSON bodies",
            artifact_type="code",
            target_path=f"src/{attack.service}/errors.py",
            suggested_diff=_error_sanitize_diff(),
            transcript=f"Error paths on {attack.service} may leak internals. Adding response sanitizer.",
        )
    if technique == "idor_under_latency":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.HYBRID,
            title="Transactional auth under DB stress",
            action="Enable RDS Multi-AZ + serializable read on ownership check",
            artifact_type="terraform",
            target_path="infra/rds.tf",
            suggested_diff=_rds_multi_az_diff(),
            transcript=f"IDOR race during DB latency on {attack.service}. Hardening DB + auth transaction.",
        )
    if technique == "dependency_blackhole":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.RESILIENCE,
            title="Enable RDS Multi-AZ",
            action="Update Terraform to set multi_az = true on payments-db",
            artifact_type="terraform",
            target_path="infra/rds.tf",
            suggested_diff=_rds_multi_az_diff(),
            transcript=f"DB blackhole on {attack.service}. Opening Multi-AZ Terraform PR.",
        )
    if technique == "pod_kill":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.RESILIENCE,
            title="Add PriorityClass and probes",
            action="chaos-critical PriorityClass + readiness/liveness probes",
            artifact_type="manifest",
            target_path=f"k8s/{attack.service}-deployment.yaml",
            suggested_diff=_priority_class_diff(attack.service) + "\n" + _probes_diff(attack.service),
            transcript=f"Pod kill on {attack.service}. Patching deployment for faster recovery.",
        )
    if technique == "network_latency":
        return BlueDefense(
            attack_id=attack.id,
            category=AttackCategory.RESILIENCE,
            title="Add circuit breaker on outbound calls",
            action="Istio VirtualService retry + outlier detection",
            artifact_type="config",
            target_path=f"mesh/{attack.service}-vs.yaml",
            suggested_diff=_istio_retry_diff(attack.service),
            transcript=f"Latency cascade to {attack.service}. Drafting Istio retry policy.",
        )
    return BlueDefense(
        attack_id=attack.id,
        category=attack.category,
        title=f"Defend against {attack.title}",
        action=attack.description,
        artifact_type="runbook",
        target_path="docs/security-runbook.md",
        suggested_diff=f"# Counter {attack.technique}\n# Service: {attack.service}",
        transcript=f"Generic defense drafted for {attack.technique} on {attack.service}.",
    )


def _jwt_hardening_diff() -> str:
    return """# JWT middleware
def validate_token(token: str) -> Claims:
    claims = jwt.decode(token, key=JWT_PUBLIC_KEY, algorithms=["RS256"])
    if claims["exp"] < time.time():
        raise Unauthorized("Token expired")
    return claims"""


def _idor_guard_diff() -> str:
    return """# GET /orders/:id
order = db.get_order(order_id)
if order.user_id != current_user.id:
    raise Forbidden("Not your order")"""


def _rate_limit_diff(service: str) -> str:
    return f"""apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: {service}-auth-ratelimit
spec:
  configPatches:
    - applyTo: HTTP_ROUTE
      match:
        route:
          name: login
      patch:
        operation: MERGE
        value:
          typed_per_filter_config:
            envoy.filters.http.local_ratelimit:
              stat_prefix: auth_ratelimit
              token_bucket:
                max_tokens: 20
                tokens_per_fill: 20
                fill_interval: 60s"""


def _session_cookie_diff() -> str:
    return """response.set_cookie(
    "session",
    value=session_id,
    httponly=True,
    secure=True,
    samesite="strict",
)"""


def _fail_closed_auth_diff() -> str:
    return """# auth middleware
try:
    identity = auth_client.verify(token, timeout=2.0)
except (Timeout, ServiceUnavailable):
    raise Unauthorized("Authentication unavailable")"""


def _error_sanitize_diff() -> str:
    return """def sanitize_error(exc: Exception) -> dict:
    return {"error": "internal_error", "request_id": request_id}
    # never include exc.args, stack, or env vars"""


def _rds_multi_az_diff() -> str:
    return """resource "aws_db_instance" "payments_db" {
  identifier = "payments-db"
  multi_az   = true   # was: false
  # ...
}"""


def _sqs_dlq_diff() -> str:
    return """resource "aws_sqs_queue" "order_events_dlq" {
  name = "order-events-dlq"
}

resource "aws_sqs_queue" "order_events" {
  name = "order-events"
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_events_dlq.arn
    maxReceiveCount     = 5
  })
}"""


def _priority_class_diff(service: str) -> str:
    return f"""apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: chaos-critical
value: 1000000
---
# patch Deployment {service}
spec:
  template:
    spec:
      priorityClassName: chaos-critical"""


def _probes_diff(service: str) -> str:
    return f"""# Deployment {service}
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15"""


def _istio_retry_diff(service: str) -> str:
    return f"""apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {service}
spec:
  http:
    - route:
        - destination:
            host: {service}
      retries:
        attempts: 3
        perTryTimeout: 2s
      timeout: 6s"""


def _client_timeout_diff() -> str:
    return """# HTTP client
timeout = httpx.Timeout(5.0, connect=2.0)
client = httpx.AsyncClient(timeout=timeout)"""
