from fastapi import APIRouter

from chaos_agent.platform.integrations_service import get_integrations_status

router = APIRouter()


@router.get("")
async def integrations() -> dict:
    items = await get_integrations_status()
    return {"integrations": items}
