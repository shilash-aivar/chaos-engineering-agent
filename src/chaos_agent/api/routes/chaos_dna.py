from fastapi import APIRouter

from chaos_agent.platform.chaos_dna_service import get_chaos_dna

router = APIRouter()


@router.get("")
async def chaos_dna(namespace: str = "staging") -> dict:
    return await get_chaos_dna(namespace)
