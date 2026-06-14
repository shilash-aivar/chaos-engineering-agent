"""Load observability-catalog.yaml — service metrics and log selectors."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CATALOG = _PROJECT_ROOT / "config" / "observability-catalog.yaml"


class ServiceObservabilitySpec(BaseModel):
    metrics: list[str] = Field(default_factory=list)
    log_selector: str = ""


class PathObservabilitySpec(BaseModel):
    services: list[str] = Field(default_factory=list)
    trace_query: str = ""


class ObservabilityCatalog(BaseModel):
    services: dict[str, ServiceObservabilitySpec] = Field(default_factory=dict)
    paths: dict[str, PathObservabilitySpec] = Field(default_factory=dict)


@lru_cache(maxsize=1)
def load_catalog(path: Optional[str] = None) -> ObservabilityCatalog:
    catalog_path = Path(path) if path else _DEFAULT_CATALOG
    if not catalog_path.exists():
        return ObservabilityCatalog()
    raw: dict[str, Any] = yaml.safe_load(catalog_path.read_text()) or {}
    services = {
        name: ServiceObservabilitySpec.model_validate(spec)
        for name, spec in (raw.get("services") or {}).items()
    }
    paths = {
        name: PathObservabilitySpec.model_validate(spec)
        for name, spec in (raw.get("paths") or {}).items()
    }
    return ObservabilityCatalog(services=services, paths=paths)


def resolve_services_for_plan(
    target_services: list[str],
    fault_targets: list[str],
    watch_metrics: list[str],
    catalog: Optional[ObservabilityCatalog] = None,
) -> list[str]:
    """Derive services to query from plan targets, faults, and metric names."""
    cat = catalog or load_catalog()
    names: set[str] = set()
    for svc in target_services + fault_targets:
        if svc:
            names.add(svc)
    for metric in watch_metrics:
        for svc in cat.services:
            if metric.startswith(svc.replace("-", "_")) or svc.replace("-", "_") in metric:
                names.add(svc)
        for prefix in ("checkout", "payments", "inventory", "payments-api", "inventory-api"):
            if metric.startswith(prefix):
                names.add(prefix if prefix != "payments" else "payments-api")
    if not names:
        names.update(cat.services.keys())
    return sorted(names)


def resolve_metrics_for_services(
    services: list[str],
    watch_metrics: list[str],
    catalog: Optional[ObservabilityCatalog] = None,
) -> list[str]:
    cat = catalog or load_catalog()
    metrics: list[str] = list(watch_metrics)
    seen = set(metrics)
    for svc in services:
        spec = cat.services.get(svc)
        if spec:
            for m in spec.metrics:
                if m not in seen:
                    metrics.append(m)
                    seen.add(m)
    return metrics
