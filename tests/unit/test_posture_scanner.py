import pytest

from chaos_agent.posture.scanner import PostureScanner


@pytest.mark.asyncio
async def test_posture_scan_includes_all_scopes() -> None:
    result = await PostureScanner("staging").scan()
    scopes = {g["scope"] for g in result["gaps"]}
    assert "k8s" in scopes
    assert "aws" in scopes
    assert "app" in scopes
    assert "deps" in scopes
    assert "observability" in scopes
    assert result["summary"]["deps"] >= 1
