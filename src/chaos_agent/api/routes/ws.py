"""WebSocket — live experiment and campaign updates."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from chaos_agent.storage.database import get_session_factory
from chaos_agent.storage.repositories.experiments import ExperimentRepository

router = APIRouter()


@router.websocket("/experiments/{experiment_id}")
async def experiment_ws(websocket: WebSocket, experiment_id: str) -> None:
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
