"""Shared graph and snapshot types."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class GraphEdgeType(str, Enum):
    K8S_SERVICE = "k8s_service"
    INGRESS = "ingress"
    RDS = "rds"
    SQS = "sqs"
    CACHE = "cache"
    HTTP_API = "http_api"
    GRPC = "grpc"
    KAFKA = "kafka"
    TRACE = "trace"


class GraphEdge(BaseModel):
    from_service: str = Field(alias="from")
    to_service: str = Field(alias="to")
    type: GraphEdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class AppService(BaseModel):
    name: str
    namespace: str
    tier: str = "standard"
    health_path: Optional[str] = None
    has_circuit_breaker: bool = False
    has_retry: bool = False
    feature_flags: list[str] = Field(default_factory=list)


class Dependency(BaseModel):
    name: str
    type: str  # postgres, redis, kafka, http, grpc
    owner_service: str
    endpoint: str
    has_timeout: bool = False
    has_retry: bool = False
    pool_size: Optional[int] = None
    third_party: bool = False


class ObservabilityTarget(BaseModel):
    name: str
    type: str  # prometheus, grafana, tempo, loki, pagerduty, github
    status: str  # ok, gap, missing
    detail: Optional[str] = None


class SnapshotContext(BaseModel):
    cluster: str = "eks-staging"
    namespace: str = "staging"
    aws_account: str = "111122223333"
    aws_region: str = "us-east-1"
    environment: str = "staging"


class InfraSnapshot(BaseModel):
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context: SnapshotContext = Field(default_factory=SnapshotContext)
    kubernetes: dict[str, Any] = Field(default_factory=dict)
    aws: dict[str, Any] = Field(default_factory=dict)
    applications: list[AppService] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    observability: list[ObservabilityTarget] = Field(default_factory=list)
    graph_edges: list[GraphEdge] = Field(default_factory=list)
