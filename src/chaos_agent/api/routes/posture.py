from fastapi import APIRouter

router = APIRouter()


@router.get("/scan")
async def scan_posture() -> dict[str, str]:
    """Run K8s + AWS posture rules against current context."""
    return {"status": "not_implemented"}
