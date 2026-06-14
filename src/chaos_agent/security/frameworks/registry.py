"""Attack framework registry — OWASP, MITRE ATT&CK, CWE Top 25, resilience."""

from __future__ import annotations

from typing import Optional

from chaos_agent.security.frameworks.cwe_top25 import CWE_TOP25_2023
from chaos_agent.security.frameworks.mitre_attack import MITRE_ATTACK_CLOUD_WEB
from chaos_agent.security.frameworks.owasp_top10 import OWASP_TOP10_2021
from chaos_agent.security.types import AttackFramework, FrameworkCategory

_FRAMEWORKS: dict[str, AttackFramework] = {
    "owasp-top10-2021": AttackFramework(
        id="owasp-top10-2021",
        name="OWASP Top 10",
        version="2021",
        description="Standard awareness document for web application security risks.",
        source_url="https://owasp.org/Top10/",
        categories=OWASP_TOP10_2021,
    ),
    "mitre-attack-enterprise": AttackFramework(
        id="mitre-attack-enterprise",
        name="MITRE ATT&CK",
        version="Enterprise (cloud/web subset)",
        description="Adversary tactics and techniques — cloud and web-relevant selection.",
        source_url="https://attack.mitre.org/",
        categories=MITRE_ATTACK_CLOUD_WEB,
    ),
    "cwe-top25-2023": AttackFramework(
        id="cwe-top25-2023",
        name="CWE Top 25",
        version="2023",
        description="Most dangerous software weakness types across industries.",
        source_url="https://cwe.mitre.org/top25/",
        categories=CWE_TOP25_2023,
    ),
    "resilience-chaos": AttackFramework(
        id="resilience-chaos",
        name="Resilience & Chaos",
        version="1.0",
        description="Infrastructure and dependency failure injection (non-security).",
        source_url="https://principlesofchaos.org/",
        categories=[
            FrameworkCategory(
                id="chaos-infra",
                name="Infrastructure faults",
                description="Pod kill, AZ impairment, network partition.",
                cwes=[],
                mitre_techniques=["T1499"],
            ),
            FrameworkCategory(
                id="chaos-deps",
                name="Dependency faults",
                description="DB blackhole, third-party timeout, queue backlog.",
                cwes=[],
                mitre_techniques=["T1499"],
            ),
            FrameworkCategory(
                id="chaos-load",
                name="Load & performance",
                description="k6 load, stress, soak paired with faults.",
                cwes=[],
                mitre_techniques=["T1499"],
            ),
        ],
    ),
}


def list_frameworks() -> list[AttackFramework]:
    return list(_FRAMEWORKS.values())


def get_framework(framework_id: str) -> Optional[AttackFramework]:
    return _FRAMEWORKS.get(framework_id)


def get_categories(framework_id: str, category_ids: Optional[list[str]] = None) -> list[FrameworkCategory]:
    fw = get_framework(framework_id)
    if fw is None:
        return []
    if not category_ids:
        return fw.categories
    return [c for c in fw.categories if c.id in category_ids]
