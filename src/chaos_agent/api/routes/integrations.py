from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from chaos_agent.platform.connector_store import get_connector_config, save_connector_config
from chaos_agent.platform.integrations_service import get_integrations_status, test_integration

router = APIRouter()


class ConnectorConfigUpdate(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)


@router.get("")
async def integrations() -> dict:
    items = await get_integrations_status()
    return {"integrations": items}


@router.get("/{integration_id}/config")
async def connector_config(integration_id: str) -> dict:
    try:
        return get_connector_config(integration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{integration_id}/config")
async def update_connector_config(integration_id: str, body: ConnectorConfigUpdate) -> dict:
    try:
        return save_connector_config(integration_id, body.values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{integration_id}/test")
async def test_integration_route(integration_id: str) -> dict:
    known = {item["id"] for item in await get_integrations_status()}
    if integration_id not in known:
        raise HTTPException(status_code=404, detail=f"Unknown integration: {integration_id}")
    return await test_integration(integration_id)
