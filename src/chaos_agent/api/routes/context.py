"""Context ingestion and analysis API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chaos_agent.context.ingest import ingest_context
from chaos_agent.context.types import ContextAnalysisResult, ContextSnapshot
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.context import ContextRepository

router = APIRouter()


class IngestRequest(BaseModel):
    repo_name: str
    namespace: str = "staging"
    terraform_files: dict[str, str] = Field(default_factory=dict)
    readme_content: Optional[str] = None
    documents: list[dict[str, str]] = Field(default_factory=list)
    code_files: dict[str, str] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    snapshot: ContextSnapshot
    analysis: ContextAnalysisResult


@router.post("/ingest", response_model=IngestResponse)
async def ingest_and_analyze(body: IngestRequest) -> IngestResponse:
    snapshot = ingest_context(
        repo_name=body.repo_name,
        namespace=body.namespace,
        terraform_files=body.terraform_files or None,
        readme_content=body.readme_content,
        documents=body.documents or None,
        code_files=body.code_files or None,
    )

    factory = get_session_factory()
    async with factory() as session:
        repo = ContextRepository(session)
        row = await repo.save_ingest(snapshot)
        analysis = await repo.run_analysis(row)

    return IngestResponse(snapshot=snapshot, analysis=analysis)


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
