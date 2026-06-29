"""Context ingestion and analysis API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chaos_agent.context.ingest import ingest_context
from chaos_agent.context.sources.github import GitHubContextPuller
from chaos_agent.context.types import ContextAnalysisResult, ContextSnapshot
from chaos_agent.context.understanding import understanding_from_snapshot
from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.platform.target_context_service import (
    get_context_by_id,
    list_target_contexts,
    probe_aws,
    probe_context,
    snapshot_builder_for_namespace,
)
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.context import ContextRepository

router = APIRouter()


@router.get("/targets")
async def get_target_contexts() -> dict:
    contexts = list_target_contexts()
    return {"contexts": contexts}


@router.get("/targets/{context_id}/probe")
async def probe_target_context(context_id: str) -> dict:
    ctx = get_context_by_id(context_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Unknown context")
    return await probe_context(ctx["namespace"], cluster=ctx.get("cluster", "eks-staging"))


class IngestRequest(BaseModel):
    repo_name: str
    namespace: str = "staging"
    terraform_files: dict[str, str] = Field(default_factory=dict)
    readme_content: Optional[str] = None
    documents: list[dict[str, str]] = Field(default_factory=list)
    code_files: dict[str, str] = Field(default_factory=dict)
    manifest_files: dict[str, str] = Field(default_factory=dict)
    raw_files: dict[str, str] = Field(default_factory=dict)


class PullGitHubRequest(BaseModel):
    namespace: str = "staging"
    path_prefix: str = ""
    repo_name: Optional[str] = None


class IngestResponse(BaseModel):
    snapshot: ContextSnapshot
    analysis: ContextAnalysisResult


async def _ingest_and_analyze(
  *,
  repo_name: str,
  namespace: str,
  terraform_files: dict[str, str] | None = None,
  readme_content: str | None = None,
  documents: list[dict[str, str]] | None = None,
  code_files: dict[str, str] | None = None,
  manifest_files: dict[str, str] | None = None,
  raw_files: dict[str, str] | None = None,
) -> IngestResponse:
    snapshot = ingest_context(
        repo_name=repo_name,
        namespace=namespace,
        terraform_files=terraform_files or None,
        readme_content=readme_content,
        documents=documents or None,
        code_files=code_files or None,
        manifest_files=manifest_files or None,
        raw_files=raw_files or None,
    )
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        row = await repo.save_ingest(snapshot)
        analysis = await repo.run_analysis(row)
    return IngestResponse(snapshot=snapshot, analysis=analysis)


@router.post("/ingest", response_model=IngestResponse)
async def ingest_and_analyze(body: IngestRequest) -> IngestResponse:
    return await _ingest_and_analyze(
        repo_name=body.repo_name,
        namespace=body.namespace,
        terraform_files=body.terraform_files,
        readme_content=body.readme_content,
        documents=body.documents,
        code_files=body.code_files,
        manifest_files=body.manifest_files,
        raw_files=body.raw_files or None,
    )


@router.post("/pull-github", response_model=IngestResponse)
async def pull_from_github(body: PullGitHubRequest) -> IngestResponse:
    puller = GitHubContextPuller()
    if not puller.configured:
        raise HTTPException(status_code=400, detail="GitHub connector not configured")
    try:
        classified, _meta = await puller.pull(body.path_prefix)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub pull failed: {exc}") from exc

    total = (
        len(classified.terraform_files)
        + len(classified.documents)
        + len(classified.manifest_files)
        + len(classified.code_files)
    )
    if total == 0:
        raise HTTPException(status_code=404, detail="No readable context files found in repository")

    repo_name = body.repo_name or f"{puller.org}/{puller.repo}"
    return await _ingest_and_analyze(
        repo_name=repo_name,
        namespace=body.namespace,
        terraform_files=classified.terraform_files,
        readme_content=classified.readme_content,
        documents=classified.documents,
        code_files=classified.code_files,
        manifest_files=classified.manifest_files,
    )


@router.get("/snapshots")
async def list_context_snapshots(namespace: str = "staging", limit: int = 20) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        rows = await repo.list_snapshots(namespace, limit=limit)
        return {
            "snapshots": [
                {
                    "id": row.id,
                    "repo_name": row.repo_name,
                    "namespace": row.namespace,
                    "ingested_at": row.ingested_at.isoformat(),
                    "has_analysis": bool(row.analysis_json),
                }
                for row in rows
            ]
        }


@router.delete("/snapshots/{snapshot_id}")
async def delete_context_snapshot(snapshot_id: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        deleted = await repo.delete(snapshot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"deleted": True, "id": snapshot_id}


@router.get("/snapshot")
async def get_latest_snapshot(namespace: str = "staging") -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        row = await repo.get_latest(namespace)
        if row is None:
            raise HTTPException(status_code=404, detail="No context snapshot found")
        snapshot = ContextRepository.row_to_snapshot(row)
        return snapshot.model_dump(mode="json")


@router.get("/snapshot/{snapshot_id}")
async def get_snapshot_by_id(snapshot_id: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        row = await repo.get_by_id(snapshot_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        return ContextRepository.row_to_snapshot(row).model_dump(mode="json")


@router.get("/analysis", response_model=ContextAnalysisResult)
async def get_latest_analysis(namespace: str = "staging", refresh: bool = False) -> ContextAnalysisResult:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        row = await repo.get_latest(namespace)
        if row is None:
            raise HTTPException(status_code=404, detail="No context snapshot found")

        if refresh or not row.analysis_json:
            return await repo.run_analysis(row)

        cached = ContextRepository.analysis_from_row(row)
        if cached is None:
            return await repo.run_analysis(row)
        return cached


@router.get("/analysis/{snapshot_id}", response_model=ContextAnalysisResult)
async def get_analysis_by_id(snapshot_id: str, refresh: bool = False) -> ContextAnalysisResult:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        row = await repo.get_by_id(snapshot_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        if refresh or not row.analysis_json:
            return await repo.run_analysis(row)
        cached = ContextRepository.analysis_from_row(row)
        if cached is None:
            return await repo.run_analysis(row)
        return cached


@router.get("/aws-probe")
async def aws_probe(namespace: str = "staging", context_id: Optional[str] = None) -> dict:
    return await probe_aws(namespace, context_id=context_id)


@router.get("/understanding")
async def get_context_understanding(namespace: str = "staging", snapshot_id: Optional[str] = None) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        if snapshot_id:
            row = await repo.get_by_id(snapshot_id)
        else:
            row = await repo.get_latest(namespace)
        if row is None:
            raise HTTPException(status_code=404, detail="No context snapshot found")
        snapshot = ContextRepository.row_to_snapshot(row)

    builder = snapshot_builder_for_namespace(namespace)
    infra = await builder.build()
    return {
        "snapshot_id": snapshot.id,
        "repo_name": snapshot.repo_name,
        "namespace": snapshot.namespace,
        "aws": {
            "source": infra.aws.get("source"),
            "region": infra.aws.get("region"),
            "account_id": infra.aws.get("account_id"),
            "fallback_reason": infra.aws.get("fallback_reason"),
        },
        "understanding": understanding_from_snapshot(snapshot, infra),
    }
