from fastapi import APIRouter

router = APIRouter()


@router.post("/campaigns")
async def start_campaign() -> dict[str, str]:
    """Start a Red vs Blue campaign in staging (referee-gated)."""
    return {"status": "not_implemented"}
