from fastapi import APIRouter

from chaos_agent.posture.scanner import PostureScanner

router = APIRouter()


@router.get("/scan")
async def scan_posture(namespace: str = "staging") -> dict:
    scanner = PostureScanner(namespace)
    return await scanner.scan()
