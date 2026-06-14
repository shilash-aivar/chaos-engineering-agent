"""GitHub integration — issues, PR comments, CI chaos gate."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from chaos_agent.config import get_settings


class GitHubClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.github_token
        self.org = settings.github_org
        self.repo = settings.github_repo
        self.default_branch = settings.github_default_branch

    @property
    def _api_base(self) -> str:
        return f"https://api.github.com/repos/{self.org}/{self.repo}"

    async def create_issue(self, title: str, body: str, labels: list[str]) -> dict[str, Any]:
        if not self.token:
            return {"number": 0, "url": "", "dry_run": True, "title": title}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._api_base}/issues",
                headers=self._headers(),
                json={"title": title, "body": body, "labels": labels},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"number": data["number"], "url": data["html_url"], "dry_run": False}

    async def create_pull_request(
        self,
        title: str,
        body: str,
        branch: str,
        file_path: str,
        file_content: str,
    ) -> dict[str, Any]:
        if not self.token or not self.org or not self.repo:
            return {
                "number": 0,
                "url": "",
                "dry_run": True,
                "title": title,
                "branch": branch,
                "message": "Set CHAOS_AGENT_GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO for live PRs",
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            ref_resp = await client.get(
                f"{self._api_base}/git/ref/heads/{self.default_branch}",
                headers=self._headers(),
            )
            if ref_resp.status_code != 200:
                return {"number": 0, "url": "", "dry_run": True, "title": title, "error": "base ref not found"}

            sha = ref_resp.json()["object"]["sha"]
            await client.post(
                f"{self._api_base}/git/refs",
                headers=self._headers(),
                json={"ref": f"refs/heads/{branch}", "sha": sha},
            )

            blob = await client.post(
                f"{self._api_base}/git/blobs",
                headers=self._headers(),
                json={"content": file_content, "encoding": "utf-8"},
            )
            blob_sha = blob.json()["sha"]

            tree = await client.post(
                f"{self._api_base}/git/trees",
                headers=self._headers(),
                json={
                    "base_tree": sha,
                    "tree": [{"path": file_path, "mode": "100644", "type": "blob", "sha": blob_sha}],
                },
            )
            tree_sha = tree.json()["sha"]

            commit = await client.post(
                f"{self._api_base}/git/commits",
                headers=self._headers(),
                json={"message": title, "tree": tree_sha, "parents": [sha]},
            )
            commit_sha = commit.json()["sha"]

            await client.patch(
                f"{self._api_base}/git/refs/heads/{branch}",
                headers=self._headers(),
                json={"sha": commit_sha},
            )

            pr = await client.post(
                f"{self._api_base}/pulls",
                headers=self._headers(),
                json={"title": title, "head": branch, "base": self.default_branch, "body": body},
            )
            pr.raise_for_status()
            data = pr.json()
            return {
                "number": data["number"],
                "url": data["html_url"],
                "dry_run": False,
                "title": title,
                "branch": branch,
            }

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
