"""Parse Kubernetes YAML manifests for declared resilience signals."""

from __future__ import annotations

import re

MANIFEST_PATTERNS = [
    (r"kind:\s*Deployment", "Kubernetes Deployment"),
    (r"kind:\s*StatefulSet", "Kubernetes StatefulSet"),
    (r"kind:\s*Service", "Kubernetes Service"),
    (r"kind:\s*HorizontalPodAutoscaler", "HPA configured"),
    (r"kind:\s*PodDisruptionBudget", "PodDisruptionBudget configured"),
    (r"readinessProbe:", "Readiness probe declared"),
    (r"livenessProbe:", "Liveness probe declared"),
    (r"priorityClassName:", "PriorityClass referenced"),
    (r"replicas:\s*(\d+)", "Replica count declared"),
    (r"resources:\s*\n\s*limits:", "Resource limits declared"),
    (r"topologySpreadConstraints:", "Topology spread configured"),
    (r"podAntiAffinity:", "Pod anti-affinity configured"),
]


def parse_manifest(content: str, filename: str = "manifest.yaml") -> list[str]:
    hints: list[str] = []
    for pattern, label in MANIFEST_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if not match:
            continue
        if pattern.startswith("replicas:") and match.group(1):
            hints.append(f"{filename}: {label} ({match.group(1)})")
        else:
            hints.append(f"{filename}: {label}")

    name_match = re.search(r"metadata:\s*\n(?:\s+.+\n)*?\s+name:\s*(\S+)", content)
    if name_match:
        hints.insert(0, f"{filename}: resource name={name_match.group(1)}")

    if not hints and content.strip():
        hints.append(f"{filename}: manifest uploaded ({len(content)} bytes)")
    return hints
