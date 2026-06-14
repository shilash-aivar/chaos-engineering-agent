"""Run all SAST scanners on ingested context."""

from __future__ import annotations

from typing import Dict, Optional

from chaos_agent.security.scanners.semgrep import scan_code
from chaos_agent.security.scanners.tfsec import scan_terraform
from chaos_agent.security.scanners.types import SastScanResult


def run_sast_scan(
    *,
    terraform_files: Optional[Dict[str, str]] = None,
    code_files: Optional[Dict[str, str]] = None,
) -> SastScanResult:
    findings = []
    scanners: list[str] = []
    simulated = False

    tf_findings, tf_scanners, tf_sim = scan_terraform(terraform_files or {})
    findings.extend(tf_findings)
    scanners.extend(tf_scanners)
    simulated = simulated or tf_sim

    code_findings, code_scanners, code_sim = scan_code(code_files or {})
    findings.extend(code_findings)
    scanners.extend(code_scanners)
    simulated = simulated or code_sim

    return SastScanResult(findings=findings, scanners_used=scanners, simulated=simulated)
