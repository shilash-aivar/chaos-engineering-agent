"""Pull declared context files from a configured GitHub repository."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from chaos_agent.config import get_settings
from chaos_agent.context.sources.files import ClassifiedFiles, classify_files

# Extensions we attempt to fetch from GitHub (skip binaries/large assets).
FETCH_EXTENSIONS = {
    ".tf",
    ".tfvars",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".py",
    ".go",
    ".js",
    ".ts",
    ".tsx",
    ".java",
    ".rb",
    ".rs",
    ".sh",
    ".dockerfile",
}
SKIP_DIRS = {
    "node_modules",
    ".git",
    "vendor",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".terraform",
}
MAX_FILES = 80
MAX_FILE_BYTES = 120_000


class GitHubContextPuller:
    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.github_token
        self.org = settings.github_org
        self.repo = settings.github_repo
        self.branch = settings.github_default_branch

    @property
    def configured(self) -> bool:
        return bool(self.token and self.org and self.repo)

    @property
    def _api_base(self) -> str:
        return f"https://api.github.com/repos/{self.org}/{self.repo}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def pull(self, path_prefix: str = "") -> tuple[ClassifiedFiles, dict[str, Any]]:
        if not self.configured:
            raise ValueError("GitHub connector not configured — set token, org, and repo in Integrations")

        prefix = path_prefix.strip("/")
        tree = await self._list_tree(prefix)
        blobs = [item for item in tree if item.get("type") == "blob" and self._should_fetch(item.get("path", ""))]
        blobs = blobs[:MAX_FILES]

        files: dict[str, str] = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for item in blobs:
                path = item["path"]
                content = await self._fetch_file(client, path)
                if content:
                    files[path] = content

        classified = classify_files(files)
        meta = {
            "source": "github",
            "org": self.org,
            "repo": self.repo,
            "branch": self.branch,
            "path_prefix": prefix or "/",
            "files_fetched": len(files),
            "terraform_files": len(classified.terraform_files),
            "documents": len(classified.documents),
            "manifest_files": len(classified.manifest_files),
            "code_files": len(classified.code_files),
        }
        return classified, meta

    def _should_fetch(self, path: str) -> bool:
        lower = path.lower()
        if any(f"/{d}/" in f"/{lower}/" or lower.startswith(f"{d}/") for d in SKIP_DIRS):
            return False
        name = lower.rsplit("/", 1)[-1]
        if name in {"readme", "readme.md", "dockerfile"}:
            return True
        if "." not in name:
            return False
        ext = "." + name.rsplit(".", 1)[-1]
        return ext in FETCH_EXTENSIONS

    async def _list_tree(self, prefix: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            ref = await client.get(
                f"{self._api_base}/git/ref/heads/{self.branch}",
                headers=self._headers(),
            )
            ref.raise_for_status()
            sha = ref.json()["object"]["sha"]

            tree_resp = await client.get(
                f"{self._api_base}/git/trees/{sha}",
                headers=self._headers(),
                params={"recursive": "1"},
            )
            tree_resp.raise_for_status()
            items = tree_resp.json().get("tree", [])

        if prefix:
            prefix_slash = f"{prefix}/"
            return [i for i in items if i.get("path", "").startswith(prefix_slash) or i.get("path") == prefix]
        return items

    async def _fetch_file(self, client: httpx.AsyncClient, path: str) -> str | None:
        resp = await client.get(
            f"{self._api_base}/contents/{path}",
            headers=self._headers(),
            params={"ref": self.branch},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("size", 0) > MAX_FILE_BYTES:
            return None
        encoding = data.get("encoding")
        raw = data.get("content", "")
        if encoding == "base64":
            try:
                return base64.b64decode(raw).decode("utf-8", errors="replace")
            except Exception:
                return None
        return raw if isinstance(raw, str) else None
