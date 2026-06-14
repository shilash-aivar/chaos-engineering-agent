from fastapi import APIRouter

from chaos_agent.platform.load_tests_data import get_load_tests_catalog

router = APIRouter()


@router.get("")
async def load_tests() -> dict:
    return get_load_tests_catalog()
