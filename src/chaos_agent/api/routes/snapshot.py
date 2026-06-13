from fastapi import APIRouter

from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.types import SnapshotContext

router = APIRouter()


@router.get("")
async def get_snapshot(namespace: str = "staging") -> dict:
    """Unified infra snapshot: K8s, AWS, app, deps, observability."""
    builder = SnapshotBuilder(namespace)
    snapshot = await builder.build(SnapshotContext(namespace=namespace))
    return snapshot.model_dump(mode="json")
