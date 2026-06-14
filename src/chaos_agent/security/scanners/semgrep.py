"""Code SAST — semgrep CLI when available, pattern heuristics otherwise."""

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
    (r"eval\s*\(", "python.lang.security.eval", "critical", "Use of eval()", "CWE-94"),
    (r"exec\s*\(", "python.lang.security.exec", "critical", "Use of exec()", "CWE-94"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "generic.secrets.hardcoded", "high", "Hardcoded password", "CWE-798"),
    (r"api[_-]?key\s*=\s*['\"]", "generic.secrets.api-key", "high", "Hardcoded API key", "CWE-798"),
    (r"execute\s*\(\s*['\"].*%s", "python.sql.format", "high", "Possible SQL string formatting", "CWE-89"),
    (r"AsyncClient\s*\(\s*\)", "python.http.no-timeout", "medium", "HTTP client without timeout", "CWE-400"),
    (r"verify\s*=\s*False", "python.ssl.verify-disabled", "high", "TLS verification disabled", "CWE-295"),
]


def _heuristic_scan(code_files: Dict[str, str]) -> list[SastFinding]:
    findings: list[SastFinding] = []
    for path, content in code_files.items():
        for line_no, line in enumerate(content.splitlines(), start=1):
            for pattern, rule_id, severity, message, cwe in _HEURISTICS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(
                        SastFinding(
                            scanner="builtin-semgrep",
                            rule_id=rule_id,
                            severity=severity,
                            message=message,
                            file_path=path,
                            cwe=cwe,
                            line=line_no,
                            simulated=True,
                        ),
                    )
    return findings


def scan_code(code_files: Dict[str, str]) -> tuple[list[SastFinding], list[str], bool]:
    if not code_files:
        return [], [], False

    if shutil.which("semgrep"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path, content in code_files.items():
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
            try:
                proc = subprocess.run(
                    [
                        "semgrep",
                        "--config=auto",
                        "--json",
                        "--quiet",
                        str(root),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    check=False,
                )
                if proc.stdout.strip():
                    data = json.loads(proc.stdout)
                    findings: list[SastFinding] = []
                    for item in data.get("results", []):
                        extra = item.get("extra", {})
                        findings.append(
                            SastFinding(
                                scanner="semgrep",
                                rule_id=item.get("check_id", "semgrep"),
                                severity=extra.get("severity", "medium"),
                                message=extra.get("message", "semgrep finding"),
                                file_path=item.get("path", "unknown"),
                                cwe=(extra.get("metadata") or {}).get("cwe"),
                                line=item.get("start", {}).get("line"),
                                simulated=False,
                            ),
                        )
                    if findings:
                        return findings, ["semgrep"], False
            except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
                pass

    findings = _heuristic_scan(code_files)
    return findings, ["builtin-semgrep"], True
