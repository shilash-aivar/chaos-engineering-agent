from fastapi import APIRouter
from pydantic import BaseModel

from chaos_agent.api import mock_data

router = APIRouter()


class StartCampaignRequest(BaseModel):
    name: str


@router.get("/campaigns")
async def list_campaigns() -> list[dict]:
    return mock_data.list_campaigns()


@router.post("/campaigns")
async def start_campaign(body: StartCampaignRequest) -> dict:
    return mock_data.start_campaign(body.name)
