from fastapi import APIRouter, HTTPException

from chaos_agent.platform.integrations_service import get_integrations_status, test_integration

router = APIRouter()


@router.get("")
async def integrations() -> dict:
    items = await get_integrations_status()
    return {"integrations": items}


@router.post("/{integration_id}/test")
async def test_integration_route(integration_id: str) -> dict:
    known = {item["id"] for item in await get_integrations_status()}
    if integration_id not in known:
        raise HTTPException(status_code=404, detail=f"Unknown integration: {integration_id}")
    return await test_integration(integration_id)
