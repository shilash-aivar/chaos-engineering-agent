"""Terraform SAST — tfsec CLI when available, regex heuristics otherwise."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

from chaos_agent.security.scanners.types import SastFinding

_HEURISTICS = [
    (r'acl\s*=\s*"public-read"', "AWS:S3.PublicAccess", "critical", "S3 bucket may be public", "CWE-200"),
    (r"0\.0\.0\.0/0", "AWS:SG.OpenIngress", "high", "Security group allows open ingress", "CWE-284"),
    (r"multi_az\s*=\s*false", "AWS:RDS.SingleAZ", "high", "RDS not Multi-AZ", "CWE-657"),
    (r"password\s*=\s*\"", "AWS:Secret.Hardcoded", "critical", "Hardcoded password in Terraform", "CWE-798"),
]


def _heuristic_scan(terraform_files: Dict[str, str]) -> list[SastFinding]:
    findings: list[SastFinding] = []
    for path, content in terraform_files.items():
        for pattern, rule_id, severity, message, cwe in _HEURISTICS:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(
                    SastFinding(
                        scanner="builtin-tf",
                        rule_id=rule_id,
                        severity=severity,
                        message=message,
                        file_path=path,
                        cwe=cwe,
                        simulated=True,
                    ),
                )
    return findings


def scan_terraform(terraform_files: Dict[str, str]) -> tuple[list[SastFinding], list[str], bool]:
    if not terraform_files:
        return [], [], False

    if shutil.which("tfsec"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path, content in terraform_files.items():
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
            try:
                proc = subprocess.run(
                    ["tfsec", str(root), "--format", "json", "--soft-fail"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                if proc.stdout.strip():
                    data = json.loads(proc.stdout)
                    results = data.get("results", data) if isinstance(data, dict) else data
                    findings: list[SastFinding] = []
                    for item in results if isinstance(results, list) else []:
                        findings.append(
                            SastFinding(
                                scanner="tfsec",
                                rule_id=item.get("rule_id", item.get("rule", "tfsec")),
                                severity=item.get("severity", "medium"),
                                message=item.get("description", item.get("summary", "tfsec finding")),
                                file_path=item.get("location", {}).get("filename", "main.tf"),
                                line=item.get("location", {}).get("start_line"),
                                simulated=False,
                            ),
                        )
                    if findings:
                        return findings, ["tfsec"], False
            except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
                pass

    findings = _heuristic_scan(terraform_files)
    return findings, ["builtin-tf"], True
