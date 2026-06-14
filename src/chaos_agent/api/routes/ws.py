"""WebSocket — live experiment and campaign updates."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chaos_agent.api.middleware.auth import verify_api_key
from chaos_agent.config import get_settings
from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/experiments/{experiment_id}")
async def experiment_ws(websocket: WebSocket, experiment_id: str) -> None:
    settings = get_settings()
    if settings.api_key:
        token = websocket.query_params.get("token") or websocket.headers.get("x-api-key")
        if not verify_api_key(token):
            await websocket.close(code=1008, reason="Unauthorized")
            return

    await websocket.accept()
    try:
        last_payload = ""
        while True:
            factory = get_session_factory()
            async with factory() as session:
                repo = ExperimentRepository(session)
                row = await repo.get(experiment_id)
                if row is None:
                    await websocket.send_json({"error": "not_found"})
                    break
                detail = await repo.detail_dict(row)
            payload = json.dumps(detail, default=str)
            if payload != last_payload:
                await websocket.send_json({"type": "experiment", "data": detail})
                last_payload = payload
            if detail["state"] in ("complete", "failed"):
                await websocket.send_json({"type": "done", "state": detail["state"]})
                break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
