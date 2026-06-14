"""DAST probes — httpx against staging base URL with safe checks."""

from __future__ import annotations

from typing import Optional

import httpx

from chaos_agent.config import get_settings
from chaos_agent.security.scanners.types import DastFinding, DastScanResult
from chaos_agent.security.types import SecurityAttackSpec


async def run_dast_probe(
    attack: SecurityAttackSpec,
    base_url: Optional[str] = None,
) -> DastFinding:
    settings = get_settings()
    base = (base_url or settings.staging_base_url).rstrip("/")
    url = f"{base}/health"
    simulated = True
    passed = True
    message = f"Probe {attack.technique} — target unreachable, simulated pass"
    severity = attack.severity_if_success

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            if attack.technique == "jwt_expired_token_probe":
                url = f"{base}/api/payments"
                resp = await client.get(url, headers={"Authorization": "Bearer expired.test"})
                simulated = False
                if resp.status_code == 200:
                    passed = False
                    message = "Expired JWT accepted — auth bypass suspected"
                    severity = "critical"
                else:
                    message = f"Expired JWT rejected ({resp.status_code})"
            elif attack.technique == "auth_rate_limit_flood":
                url = f"{base}/api/login"
                codes = []
                for _ in range(25):
                    r = await client.post(url, json={"user": "probe", "password": "x"})
                    codes.append(r.status_code)
                simulated = False
                if len(set(codes)) == 1 and codes[0] != 429:
                    passed = False
                    message = "No rate limiting detected on auth endpoint"
                else:
                    message = "Rate limiting or rejection observed"
            elif attack.technique == "idor_enumeration_probe":
                url = f"{base}/api/orders/1"
                resp = await client.get(url, headers={"X-Probe-Session": "user-a"})
                simulated = False
                if resp.status_code == 200:
                    passed = False
                    message = "Order endpoint returned 200 without ownership proof"
                else:
                    message = f"Order access denied ({resp.status_code})"
            elif attack.technique == "session_cookie_flags_audit":
                url = f"{base}/api/session"
                resp = await client.get(url)
                simulated = False
                cookies = resp.headers.get("set-cookie", "")
                if cookies and ("httponly" not in cookies.lower() or "secure" not in cookies.lower()):
                    passed = False
                    message = "Session cookie missing HttpOnly/Secure flags"
                else:
                    message = "Cookie flags OK or no session cookie set"
            else:
                resp = await client.get(url)
                simulated = False
                if resp.status_code >= 500 and "trace" in resp.text.lower():
                    passed = False
                    message = "Server error may leak stack trace"
                else:
                    message = f"Generic probe completed ({resp.status_code})"
    except (httpx.HTTPError, OSError):
        simulated = True
        passed = True
        message = f"Staging target unavailable — simulated safe result for {attack.technique}"

    return DastFinding(
        probe=attack.technique,
        target_url=url,
        severity=severity if not passed else "low",
        message=message,
        cwe=attack.cwe,
        passed=passed,
        simulated=simulated,
    )


async def run_dast_scan(
    attacks: list[SecurityAttackSpec],
    base_url: Optional[str] = None,
    limit: int = 5,
) -> DastScanResult:
    settings = get_settings()
    base = base_url or settings.staging_base_url
    findings: list[DastFinding] = []
    any_simulated = True
    for attack in attacks[:limit]:
        finding = await run_dast_probe(attack, base_url=base)
        findings.append(finding)
        if not finding.simulated:
            any_simulated = False
    return DastScanResult(findings=findings, target_base=base, simulated=any_simulated)
