"""Observability correlator API — fault-window evidence and backend status."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from chaos_agent.observability.capture import capture_experiment_evidence
from chaos_agent.observability.catalog import load_catalog
from chaos_agent.observability.correlator import ObservabilityCorrelator
from chaos_agent.observability.types import FaultWindowEvidence
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()
_correlator = ObservabilityCorrelator()


@router.get("/status")
async def observability_status() -> dict:
    status = await _correlator.backend_status()
    return status.model_dump()


@router.get("/catalog")
async def observability_catalog() -> dict:
    catalog = load_catalog()
    return {
        "services": {
            name: {"metrics": spec.metrics, "log_selector": spec.log_selector}
            for name, spec in catalog.services.items()
        },
        "paths": {
            name: {"services": spec.services, "trace_query": spec.trace_query}
            for name, spec in catalog.paths.items()
        },
    }


@router.get("/evidence/{experiment_id}")
async def get_experiment_evidence(experiment_id: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        repo = ExperimentRepository(session)
        row = await repo.get(experiment_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        if not row.evidence_json:
            raise HTTPException(status_code=404, detail="Evidence not yet captured for this experiment")
        evidence = FaultWindowEvidence.model_validate_json(row.evidence_json)
        return evidence.model_dump(mode="json")


@router.post("/evidence/{experiment_id}/capture")
async def capture_evidence(experiment_id: str) -> dict:
    evidence = await capture_experiment_evidence(experiment_id)
    return evidence.model_dump(mode="json")
