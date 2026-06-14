"""Parse README and docs for declared reliability/HA claims."""

from __future__ import annotations

import re

from chaos_agent.context.types import DeclaredDocument

CLAIM_PATTERNS = [
    (r"multi[- ]?az", "Claims Multi-AZ database deployment"),
    (r"high availability|highly available|\bHA\b", "Claims high availability"),
    (r"circuit breaker", "Documents circuit breaker usage"),
    (r"retry|retries", "Documents retry policy"),
    (r"timeout", "Documents timeout configuration"),
    (r"SLO|error budget", "Defines SLO or error budget"),
    (r"prometheus|grafana|datadog", "References monitoring stack"),
    (r"dead letter|DLQ", "Documents dead-letter queue"),
    (r"autoscaling|HPA|horizontal pod", "Documents autoscaling"),
    (r"connection pool|pool size", "Documents DB connection pool"),
]


def parse_document(content: str, name: str = "README.md", doc_type: str = "readme") -> DeclaredDocument:
    claims: list[str] = []
    lower = content.lower()
    for pattern, label in CLAIM_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            claims.append(label)

    excerpt = content[:800].strip()
    if len(content) > 800:
        excerpt += "\n…"

    return DeclaredDocument(
        name=name,
        doc_type=doc_type,
        claims=claims,
        raw_excerpt=excerpt,
    )
