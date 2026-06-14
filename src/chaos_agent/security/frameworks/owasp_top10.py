"""OWASP Top 10 (2021) — categories, CWEs, and representative CVE classes."""

from __future__ import annotations

from chaos_agent.security.types import CweEntry, FrameworkCategory

OWASP_TOP10_2021: list[FrameworkCategory] = [
    FrameworkCategory(
        id="A01",
        name="Broken Access Control",
        description="Failures to enforce authorization on objects, functions, and fields.",
        cwes=[
            CweEntry(id="CWE-639", name="Authorization bypass through user-controlled key", example_cves=["CVE-2021-44228", "CVE-2023-22527"]),
            CweEntry(id="CWE-22", name="Path traversal", example_cves=["CVE-2021-41773", "CVE-2023-4966"]),
            CweEntry(id="CWE-352", name="Cross-site request forgery", example_cves=["CVE-2021-22911", "CVE-2022-23521"]),
            CweEntry(id="CWE-425", name="Direct request (forced browsing)", example_cves=["CVE-2020-14179", "CVE-2022-46166"]),
        ],
        mitre_techniques=["T1190", "T1068"],
    ),
    FrameworkCategory(
        id="A02",
        name="Cryptographic Failures",
        description="Weak or missing encryption for data in transit and at rest.",
        cwes=[
            CweEntry(id="CWE-319", name="Cleartext transmission of sensitive information", example_cves=["CVE-2020-8209", "CVE-2021-34473"]),
            CweEntry(id="CWE-798", name="Use of hard-coded credentials", example_cves=["CVE-2021-21972", "CVE-2023-27350"]),
            CweEntry(id="CWE-326", name="Inadequate encryption strength", example_cves=["CVE-2022-0778", "CVE-2023-0286"]),
            CweEntry(id="CWE-311", name="Missing encryption of sensitive data", example_cves=["CVE-2020-1472", "CVE-2021-26855"]),
        ],
        mitre_techniques=["T1552", "T1040"],
    ),
    FrameworkCategory(
        id="A03",
        name="Injection",
        description="SQL, NoSQL, OS, and LDAP injection when untrusted data is sent to an interpreter.",
        cwes=[
            CweEntry(id="CWE-89", name="SQL injection", example_cves=["CVE-2021-44228", "CVE-2023-34362"]),
            CweEntry(id="CWE-79", name="Cross-site scripting (XSS)", example_cves=["CVE-2021-22986", "CVE-2022-41040"]),
            CweEntry(id="CWE-78", name="OS command injection", example_cves=["CVE-2021-26084", "CVE-2022-26134"]),
            CweEntry(id="CWE-943", name="NoSQL injection", example_cves=["CVE-2021-22991", "CVE-2023-28432"]),
        ],
        mitre_techniques=["T1190", "T1059"],
    ),
    FrameworkCategory(
        id="A04",
        name="Insecure Design",
        description="Missing or ineffective control design — threats modeled without secure patterns.",
        cwes=[
            CweEntry(id="CWE-840", name="Business logic errors", example_cves=["CVE-2021-22901", "CVE-2022-41082"]),
            CweEntry(id="CWE-733", name="Compiler optimization removing security code", example_cves=["CVE-2022-21449"]),
            CweEntry(id="CWE-657", name="Violation of secure design principles", example_cves=["CVE-2021-26855", "CVE-2023-4966"]),
        ],
        mitre_techniques=["T1190", "T1078"],
    ),
    FrameworkCategory(
        id="A05",
        name="Security Misconfiguration",
        description="Unsafe defaults, open cloud storage, verbose errors, unnecessary features enabled.",
        cwes=[
            CweEntry(id="CWE-16", name="Configuration", example_cves=["CVE-2021-21985", "CVE-2022-26148"]),
            CweEntry(id="CWE-209", name="Information exposure through error message", example_cves=["CVE-2021-41773", "CVE-2023-22515"]),
            CweEntry(id="CWE-200", name="Exposure of sensitive information", example_cves=["CVE-2021-21972", "CVE-2022-41023"]),
            CweEntry(id="CWE-1188", name="Insecure default initialization of resource", example_cves=["CVE-2020-5902", "CVE-2023-3519"]),
        ],
        mitre_techniques=["T1190", "T1078"],
    ),
    FrameworkCategory(
        id="A06",
        name="Vulnerable and Outdated Components",
        description="Unpatched libraries, frameworks, and dependencies with known CVEs.",
        cwes=[
            CweEntry(id="CWE-1104", name="Use of unmaintained third-party components", example_cves=["CVE-2021-44228", "CVE-2022-22965"]),
            CweEntry(id="CWE-1035", name="OWASP Top 10 2021 Category A06", example_cves=["CVE-2023-34362", "CVE-2024-3094"]),
            CweEntry(id="CWE-1395", name="Dependency on vulnerable third-party component", example_cves=["CVE-2021-45046", "CVE-2023-4863"]),
        ],
        mitre_techniques=["T1190", "T1203"],
    ),
    FrameworkCategory(
        id="A07",
        name="Identification and Authentication Failures",
        description="Broken auth — session fixation, weak credentials, missing MFA.",
        cwes=[
            CweEntry(id="CWE-287", name="Improper authentication", example_cves=["CVE-2021-22911", "CVE-2023-22527"]),
            CweEntry(id="CWE-306", name="Missing authentication for critical function", example_cves=["CVE-2021-21985", "CVE-2022-46166"]),
            CweEntry(id="CWE-307", name="Improper restriction of excessive auth attempts", example_cves=["CVE-2020-14179", "CVE-2022-23521"]),
            CweEntry(id="CWE-384", name="Session fixation", example_cves=["CVE-2021-22901", "CVE-2023-4966"]),
        ],
        mitre_techniques=["T1078", "T1110"],
    ),
    FrameworkCategory(
        id="A08",
        name="Software and Data Integrity Failures",
        description="Unsigned updates, insecure CI/CD, deserialization without integrity checks.",
        cwes=[
            CweEntry(id="CWE-494", name="Download of code without integrity check", example_cves=["CVE-2021-44228", "CVE-2023-50164"]),
            CweEntry(id="CWE-502", name="Deserialization of untrusted data", example_cves=["CVE-2022-22965", "CVE-2023-22527"]),
            CweEntry(id="CWE-829", name="Inclusion of functionality from untrusted control sphere", example_cves=["CVE-2021-26084", "CVE-2022-41040"]),
        ],
        mitre_techniques=["T1195", "T1554"],
    ),
    FrameworkCategory(
        id="A09",
        name="Security Logging and Monitoring Failures",
        description="Breaches undetected — insufficient audit, alerting, and traceability.",
        cwes=[
            CweEntry(id="CWE-778", name="Insufficient logging", example_cves=["CVE-2021-26855", "CVE-2022-41082"]),
            CweEntry(id="CWE-117", name="Improper output neutralization for logs", example_cves=["CVE-2021-44228", "CVE-2023-22515"]),
            CweEntry(id="CWE-223", name="Omission of security-relevant information", example_cves=["CVE-2020-1472", "CVE-2022-26134"]),
        ],
        mitre_techniques=["T1070", "T1562"],
    ),
    FrameworkCategory(
        id="A10",
        name="Server-Side Request Forgery (SSRF)",
        description="Fetching remote resources without validating user-supplied URLs.",
        cwes=[
            CweEntry(id="CWE-918", name="Server-side request forgery", example_cves=["CVE-2021-26855", "CVE-2023-34362"]),
            CweEntry(id="CWE-441", name="Unintended proxy / intermediary", example_cves=["CVE-2021-22986", "CVE-2022-41023"]),
        ],
        mitre_techniques=["T1190", "T1090"],
    ),
]
