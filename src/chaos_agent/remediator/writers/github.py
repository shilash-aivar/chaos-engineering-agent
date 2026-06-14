"""Create GitHub issues from remediation findings."""

from __future__ import annotations

from typing import Any

from chaos_agent.integrations.github.client import GitHubClient
from chaos_agent.remediator.models import RemediationFinding


async def create_tickets(findings: list[RemediationFinding]) -> list[RemediationFinding]:
    client = GitHubClient()
    updated: list[RemediationFinding] = []

    for finding in findings:
        labels = ["chaos-agent", "remediation", finding.severity.value, finding.scope]
        body = (
            f"## {finding.title}\n\n"
            f"**Severity:** {finding.severity.value}\n"
            f"**Scope:** {finding.scope}\n\n"
            f"### Evidence\n"
            + "\n".join(f"- {e}" for e in finding.evidence)
            + f"\n\n### Prescription\n{finding.prescription}\n\n"
        )
        if finding.suggested_diff:
            body += f"### Suggested change\n```\n{finding.suggested_diff}\n```\n"
        if finding.verification:
            body += f"\n### Verification\n{finding.verification}\n"
        if finding.experiment_id:
            body += f"\n_Experiment: `{finding.experiment_id}`_\n"

        result: dict[str, Any] = await client.create_issue(
            title=f"[Chaos] {finding.title}",
            body=body,
            labels=labels,
        )
        finding.ticket_number = int(result.get("number") or 0) or None
        finding.ticket_url = str(result.get("url") or "") or None
        finding.status = "in_progress" if finding.ticket_number else "open"
        updated.append(finding)

    return updated


async def create_pull_requests(findings: list[RemediationFinding]) -> list[RemediationFinding]:
    """Open PRs for findings with code/terraform/manifest artifacts."""
    client = GitHubClient()
    pr_types = {"code", "terraform", "manifest", "config"}
    updated: list[RemediationFinding] = []

    for finding in findings:
        if finding.artifact_type not in pr_types or not finding.suggested_diff:
            updated.append(finding)
            continue
        if finding.pr_number:
            updated.append(finding)
            continue

        title = f"[Remediator] {finding.title}"
        body = (
            f"## Chaos Agent — Remediation PR\n\n"
            f"**Prescription:** {finding.prescription}\n\n"
            f"**Evidence:**\n" + "\n".join(f"- {e}" for e in finding.evidence) + "\n\n"
            f"_Auto-generated. Review before merge._"
        )
        branch = f"remediate/{finding.id}"
        path = finding.target_path or f"docs/runbooks/{finding.id}.md"
        result = await client.create_pull_request(
            title=title,
            body=body,
            branch=branch,
            file_path=path,
            file_content=finding.suggested_diff,
        )
        finding.pr_number = int(result.get("number") or 0) or None
        finding.pr_url = str(result.get("url") or "") or None
        if finding.pr_number:
            finding.status = "in_progress"
        updated.append(finding)

    return updated
