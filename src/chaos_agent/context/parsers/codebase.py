"""Extract resilience hints from uploaded code snippets."""

from __future__ import annotations

import re

HINT_PATTERNS = [
    (r"http\.Client|requests\.(get|post)|httpx\.", "HTTP client usage detected"),
    (r"pool_size|max_connections|MaxOpenConns", "Connection pool configuration found"),
    (r"@retry|retry\.|retries\s*=", "Retry logic in code"),
    (r"CircuitBreaker|circuit.?breaker", "Circuit breaker in code"),
    (r"timeout\s*[=:]", "Timeout setting in code"),
    (r"readinessProbe|livenessProbe", "K8s probe in manifest"),
    (r"HorizontalPodAutoscaler|autoscaling/v2", "HPA manifest in repo"),
]


def parse_code_snippet(content: str, filename: str = "snippet") -> list[str]:
    hints: list[str] = []
    for pattern, label in HINT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            hints.append(f"{filename}: {label}")
    if not hints and content.strip():
        hints.append(f"{filename}: uploaded ({len(content)} bytes) — no resilience patterns matched")
    return hints
