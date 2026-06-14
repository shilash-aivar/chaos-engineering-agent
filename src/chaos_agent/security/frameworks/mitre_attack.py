"""MITRE ATT&CK Enterprise — cloud/web-relevant techniques for staging probes."""

from __future__ import annotations

from chaos_agent.security.types import CweEntry, FrameworkCategory

MITRE_ATTACK_CLOUD_WEB: list[FrameworkCategory] = [
    FrameworkCategory(
        id="T1190",
        name="Exploit Public-Facing Application",
        description="Exploit weaknesses in Internet-facing apps to gain initial access.",
        cwes=[
            CweEntry(id="CWE-79", name="XSS", example_cves=["CVE-2022-41040", "CVE-2023-22527"]),
            CweEntry(id="CWE-89", name="SQL injection", example_cves=["CVE-2021-44228", "CVE-2023-34362"]),
            CweEntry(id="CWE-918", name="SSRF", example_cves=["CVE-2021-26855", "CVE-2023-4966"]),
        ],
        mitre_techniques=["T1190"],
    ),
    FrameworkCategory(
        id="T1078",
        name="Valid Accounts",
        description="Use stolen or default credentials to access systems.",
        cwes=[
            CweEntry(id="CWE-287", name="Improper authentication", example_cves=["CVE-2021-22911", "CVE-2023-22515"]),
            CweEntry(id="CWE-798", name="Hard-coded credentials", example_cves=["CVE-2021-21972", "CVE-2023-27350"]),
        ],
        mitre_techniques=["T1078"],
    ),
    FrameworkCategory(
        id="T1110",
        name="Brute Force",
        description="Password guessing, credential stuffing, password spraying.",
        cwes=[
            CweEntry(id="CWE-307", name="Missing rate limiting on auth", example_cves=["CVE-2020-14179", "CVE-2022-23521"]),
            CweEntry(id="CWE-521", name="Weak password requirements", example_cves=["CVE-2021-22901", "CVE-2022-46166"]),
        ],
        mitre_techniques=["T1110"],
    ),
    FrameworkCategory(
        id="T1059",
        name="Command and Scripting Interpreter",
        description="Abuse command interpreters through injection in app inputs.",
        cwes=[
            CweEntry(id="CWE-78", name="OS command injection", example_cves=["CVE-2021-26084", "CVE-2022-26134"]),
            CweEntry(id="CWE-94", name="Code injection", example_cves=["CVE-2022-22965", "CVE-2023-22527"]),
        ],
        mitre_techniques=["T1059"],
    ),
    FrameworkCategory(
        id="T1552",
        name="Unsecured Credentials",
        description="Credentials in files, env vars, repos, or misconfigured secrets stores.",
        cwes=[
            CweEntry(id="CWE-798", name="Hard-coded credentials", example_cves=["CVE-2021-21972", "CVE-2023-27350"]),
            CweEntry(id="CWE-312", name="Cleartext storage of sensitive information", example_cves=["CVE-2020-8209", "CVE-2021-34473"]),
        ],
        mitre_techniques=["T1552"],
    ),
    FrameworkCategory(
        id="T1499",
        name="Endpoint Denial of Service",
        description="Disrupt availability — pairs with chaos resilience testing.",
        cwes=[
            CweEntry(id="CWE-400", name="Uncontrolled resource consumption", example_cves=["CVE-2021-22986", "CVE-2022-26148"]),
            CweEntry(id="CWE-770", name="Allocation without limits", example_cves=["CVE-2021-44228", "CVE-2023-44487"]),
        ],
        mitre_techniques=["T1499"],
    ),
    FrameworkCategory(
        id="T1562",
        name="Impair Defenses",
        description="Disable logging, monitoring, or security tools.",
        cwes=[
            CweEntry(id="CWE-778", name="Insufficient logging", example_cves=["CVE-2021-26855", "CVE-2022-41082"]),
            CweEntry(id="CWE-223", name="Omission of security-relevant information", example_cves=["CVE-2020-1472", "CVE-2022-26134"]),
        ],
        mitre_techniques=["T1562"],
    ),
    FrameworkCategory(
        id="T1195",
        name="Supply Chain Compromise",
        description="Manipulate software dependencies or update channels.",
        cwes=[
            CweEntry(id="CWE-494", name="Download without integrity check", example_cves=["CVE-2021-44228", "CVE-2024-3094"]),
            CweEntry(id="CWE-829", name="Untrusted functionality inclusion", example_cves=["CVE-2021-26084", "CVE-2023-50164"]),
        ],
        mitre_techniques=["T1195"],
    ),
]
