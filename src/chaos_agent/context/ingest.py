"""Ingest user-provided Terraform, docs, manifests, and code into declared context."""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from chaos_agent.context.parsers.codebase import parse_code_snippet
from chaos_agent.context.parsers.docs import parse_document
from chaos_agent.context.parsers.manifests import parse_manifest
from chaos_agent.context.parsers.terraform import parse_terraform
from chaos_agent.context.sources.files import ClassifiedFiles, classify_files
from chaos_agent.context.types import ContextSnapshot, DeclaredContext


def build_declared_context(
    *,
    repo_name: str,
    terraform_files: Optional[Dict[str, str]] = None,
    readme_content: Optional[str] = None,
    documents: Optional[List[dict[str, str]]] = None,
    code_files: Optional[Dict[str, str]] = None,
    manifest_files: Optional[Dict[str, str]] = None,
) -> DeclaredContext:
    resources = []
    for path, content in (terraform_files or {}).items():
        resources.extend(parse_terraform(content, source_file=path))

    docs = []
    if readme_content:
        docs.append(parse_document(readme_content, name="README.md", doc_type="readme"))
    for doc in documents or []:
        docs.append(
            parse_document(
                doc.get("content", ""),
                name=doc.get("name", "document.md"),
                doc_type=doc.get("type", "doc"),
            ),
        )

    hints: list[str] = []
    for path, content in (code_files or {}).items():
        hints.extend(parse_code_snippet(content, filename=path))

    manifest_hints: list[str] = []
    for path, content in (manifest_files or {}).items():
        manifest_hints.extend(parse_manifest(content, filename=path))

    return DeclaredContext(
        repo_name=repo_name,
        terraform_resources=resources,
        documents=docs,
        code_hints=hints,
        manifest_hints=manifest_hints,
        terraform_sources=dict(terraform_files or {}),
        code_sources=dict(code_files or {}),
        manifest_sources=dict(manifest_files or {}),
    )


def build_declared_from_classified(repo_name: str, classified: ClassifiedFiles) -> DeclaredContext:
    return build_declared_context(
        repo_name=repo_name,
        terraform_files=classified.terraform_files,
        readme_content=classified.readme_content,
        documents=classified.documents,
        code_files=classified.code_files,
        manifest_files=classified.manifest_files,
    )


def ingest_context(
    *,
    repo_name: str,
    namespace: str = "staging",
    terraform_files: Optional[Dict[str, str]] = None,
    readme_content: Optional[str] = None,
    documents: Optional[List[dict[str, str]]] = None,
    code_files: Optional[Dict[str, str]] = None,
    manifest_files: Optional[Dict[str, str]] = None,
    raw_files: Optional[Dict[str, str]] = None,
) -> ContextSnapshot:
    if raw_files:
        classified = classify_files(raw_files)
        declared = build_declared_from_classified(repo_name, classified)
    else:
        declared = build_declared_context(
            repo_name=repo_name,
            terraform_files=terraform_files,
            readme_content=readme_content,
            documents=documents,
            code_files=code_files,
            manifest_files=manifest_files,
        )
    return ContextSnapshot(
        id=f"ctx-{uuid.uuid4().hex[:12]}",
        repo_name=repo_name,
        namespace=namespace,
        declared=declared,
    )
