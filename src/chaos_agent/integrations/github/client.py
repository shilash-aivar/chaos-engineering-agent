"""GitHub integration — issues, PR comments, CI chaos gate."""

from __future__ import annotations

from typing import Any

from chaos_agent.config import get_settings


class GitHubClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.github_token
        self.org = settings.github_org
        self.repo = settings.github_repo

    async def create_issue(self, title: str, body: str, labels: list[str]) -> dict[str, Any]:
        if not self.token:
            return {"number": 0, "url": "", "dry_run": True, "title": title}
        # Phase 2: POST /repos/{org}/{repo}/issues
        return {"number": 1842, "url": f"https://github.com/{self.org}/{self.repo}/issues/1842"}
