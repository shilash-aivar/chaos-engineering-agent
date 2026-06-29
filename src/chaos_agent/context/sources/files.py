"""Classify repo/upload files into declared-context buckets."""

from __future__ import annotations

from dataclasses import dataclass, field

TF_EXTENSIONS = {".tf", ".tfvars"}
DOC_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}
DOC_NAMES = {"readme", "readme.md", "contributing.md", "architecture.md", "runbook.md"}
MANIFEST_EXTENSIONS = {".yaml", ".yml"}
CODE_EXTENSIONS = {
    ".py",
    ".go",
    ".js",
    ".ts",
    ".tsx",
    ".java",
    ".rb",
    ".rs",
    ".php",
    ".cs",
    ".kt",
    ".swift",
    ".sh",
    ".dockerfile",
}


@dataclass
class ClassifiedFiles:
    terraform_files: dict[str, str] = field(default_factory=dict)
    documents: list[dict[str, str]] = field(default_factory=list)
    manifest_files: dict[str, str] = field(default_factory=dict)
    code_files: dict[str, str] = field(default_factory=dict)
    readme_content: str | None = None


def classify_files(files: dict[str, str]) -> ClassifiedFiles:
    """Split path→content map into terraform, docs, manifests, and code."""
    result = ClassifiedFiles()
    for path, content in files.items():
        if not content.strip():
            continue
        lower = path.lower()
        name = lower.rsplit("/", 1)[-1]
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""

        if ext in TF_EXTENSIONS or "/terraform/" in lower or lower.startswith("terraform/"):
            result.terraform_files[path] = content
            continue

        if name in DOC_NAMES or ext in DOC_EXTENSIONS:
            doc_type = "readme" if "readme" in name else "doc"
            if doc_type == "readme" and result.readme_content is None:
                result.readme_content = content
            result.documents.append({"name": path, "content": content, "type": doc_type})
            continue

        if ext in MANIFEST_EXTENSIONS or any(
            marker in lower for marker in ("/k8s/", "/kubernetes/", "/manifests/", "/deploy/", "/helm/")
        ):
            result.manifest_files[path] = content
            continue

        if ext in CODE_EXTENSIONS or ext == "":
            result.code_files[path] = content

    return result
