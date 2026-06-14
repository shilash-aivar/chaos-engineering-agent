"""CWE Top 25 — most dangerous software weaknesses (2023)."""

from __future__ import annotations

from chaos_agent.security.types import CweEntry, FrameworkCategory

CWE_TOP25_2023: list[FrameworkCategory] = [
    FrameworkCategory(id="CWE-787", name="Out-of-bounds Write", description="Memory corruption via bounds violation.", cwes=[CweEntry(id="CWE-787", name="Out-of-bounds Write", example_cves=["CVE-2023-4863", "CVE-2022-3602"])]),
    FrameworkCategory(id="CWE-79", name="Cross-site Scripting", description="Reflected/stored XSS in web apps.", cwes=[CweEntry(id="CWE-79", name="XSS", example_cves=["CVE-2022-41040", "CVE-2023-22527"])]),
    FrameworkCategory(id="CWE-89", name="SQL Injection", description="Dynamic SQL built from untrusted input.", cwes=[CweEntry(id="CWE-89", name="SQL injection", example_cves=["CVE-2021-44228", "CVE-2023-34362"])]),
    FrameworkCategory(id="CWE-416", name="Use After Free", description="Memory reuse after free.", cwes=[CweEntry(id="CWE-416", name="Use after free", example_cves=["CVE-2023-4863", "CVE-2022-22620"])]),
    FrameworkCategory(id="CWE-78", name="OS Command Injection", description="Shell metacharacters in system calls.", cwes=[CweEntry(id="CWE-78", name="Command injection", example_cves=["CVE-2021-26084", "CVE-2022-26134"])]),
    FrameworkCategory(id="CWE-20", name="Improper Input Validation", description="Missing validation on untrusted input.", cwes=[CweEntry(id="CWE-20", name="Input validation", example_cves=["CVE-2021-22986", "CVE-2023-4966"])]),
    FrameworkCategory(id="CWE-125", name="Out-of-bounds Read", description="Read past buffer end.", cwes=[CweEntry(id="CWE-125", name="OOB read", example_cves=["CVE-2022-0778", "CVE-2023-0286"])]),
    FrameworkCategory(id="CWE-22", name="Path Traversal", description="../ sequences reach unintended files.", cwes=[CweEntry(id="CWE-22", name="Path traversal", example_cves=["CVE-2021-41773", "CVE-2023-4966"])]),
    FrameworkCategory(id="CWE-352", name="CSRF", description="Forged cross-site requests.", cwes=[CweEntry(id="CWE-352", name="CSRF", example_cves=["CVE-2021-22911", "CVE-2022-23521"])]),
    FrameworkCategory(id="CWE-434", name="Unrestricted Upload", description="Malicious file upload.", cwes=[CweEntry(id="CWE-434", name="File upload", example_cves=["CVE-2021-22901", "CVE-2022-41082"])]),
    FrameworkCategory(id="CWE-862", name="Missing Authorization", description="No authz check on sensitive action.", cwes=[CweEntry(id="CWE-862", name="Missing authorization", example_cves=["CVE-2023-22527", "CVE-2022-46166"])]),
    FrameworkCategory(id="CWE-476", name="NULL Pointer Dereference", description="Deref null causing DoS.", cwes=[CweEntry(id="CWE-476", name="NULL deref", example_cves=["CVE-2021-21985", "CVE-2022-26148"])]),
    FrameworkCategory(id="CWE-287", name="Improper Authentication", description="Auth bypass or weak session.", cwes=[CweEntry(id="CWE-287", name="Auth failure", example_cves=["CVE-2021-22911", "CVE-2023-22515"])]),
    FrameworkCategory(id="CWE-190", name="Integer Overflow", description="Wraparound in size calculations.", cwes=[CweEntry(id="CWE-190", name="Integer overflow", example_cves=["CVE-2022-21449", "CVE-2021-34473"])]),
    FrameworkCategory(id="CWE-502", name="Deserialization", description="Untrusted object deserialization.", cwes=[CweEntry(id="CWE-502", name="Deserialization", example_cves=["CVE-2022-22965", "CVE-2023-22527"])]),
    FrameworkCategory(id="CWE-77", name="Command Injection", description="Shell injection variant.", cwes=[CweEntry(id="CWE-77", name="Command injection", example_cves=["CVE-2021-26084", "CVE-2022-26134"])]),
    FrameworkCategory(id="CWE-119", name="Buffer Overflow", description="Classic stack/heap overflow.", cwes=[CweEntry(id="CWE-119", name="Buffer overflow", example_cves=["CVE-2023-4863", "CVE-2022-3602"])]),
    FrameworkCategory(id="CWE-798", name="Hard-coded Credentials", description="Secrets in source or config.", cwes=[CweEntry(id="CWE-798", name="Hard-coded creds", example_cves=["CVE-2021-21972", "CVE-2023-27350"])]),
    FrameworkCategory(id="CWE-918", name="SSRF", description="Server fetches attacker-controlled URL.", cwes=[CweEntry(id="CWE-918", name="SSRF", example_cves=["CVE-2021-26855", "CVE-2023-34362"])]),
    FrameworkCategory(id="CWE-306", name="Missing Authentication", description="Sensitive endpoint without auth.", cwes=[CweEntry(id="CWE-306", name="Missing auth", example_cves=["CVE-2021-21985", "CVE-2022-46166"])]),
    FrameworkCategory(id="CWE-362", name="Race Condition", description="TOCTOU concurrency bugs.", cwes=[CweEntry(id="CWE-362", name="Race condition", example_cves=["CVE-2022-21449", "CVE-2023-4966"])]),
    FrameworkCategory(id="CWE-269", name="Improper Privilege Management", description="Excessive privileges assigned.", cwes=[CweEntry(id="CWE-269", name="Privilege mgmt", example_cves=["CVE-2020-1472", "CVE-2021-26855"])]),
    FrameworkCategory(id="CWE-94", name="Code Injection", description="Dynamic code evaluation.", cwes=[CweEntry(id="CWE-94", name="Code injection", example_cves=["CVE-2022-22965", "CVE-2023-22527"])]),
    FrameworkCategory(id="CWE-863", name="Incorrect Authorization", description="Authz logic errors (IDOR).", cwes=[CweEntry(id="CWE-863", name="Incorrect authz", example_cves=["CVE-2023-22527", "CVE-2022-46166"])]),
    FrameworkCategory(id="CWE-276", name="Incorrect Default Permissions", description="World-readable sensitive files.", cwes=[CweEntry(id="CWE-276", name="Default permissions", example_cves=["CVE-2020-5902", "CVE-2021-21972"])]),
]
