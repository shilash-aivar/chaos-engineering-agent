from fastapi import APIRouter

from chaos_agent.graph.snapshot import SnapshotBuilder
from chaos_agent.graph.provenance import snapshot_is_live, snapshot_provenance
from chaos_agent.graph.types import SnapshotContext

router = APIRouter()


@router.get("")
async def get_snapshot(namespace: str = "staging") -> dict:
    """Unified infra snapshot: K8s, AWS, app, deps, observability."""
    builder = SnapshotBuilder(namespace)
    snapshot = await builder.build(SnapshotContext(namespace=namespace))
    data = snapshot.model_dump(mode="json")
    data["collection_sources"] = snapshot_provenance(snapshot)
    data["live_data"] = snapshot_is_live(snapshot)
    return data
