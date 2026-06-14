"""Slack notifications — approvals, SLO breaches, campaign events."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from chaos_agent.config import get_settings

logger = logging.getLogger(__name__)


class SlackClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.token = settings.slack_bot_token
        self.webhook_url = settings.slack_webhook_url
        self.channel = settings.slack_approval_channel

    @property
    def available(self) -> bool:
        return bool(self.token or self.webhook_url)

    async def post_message(self, text: str, *, blocks: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
        if not self.available:
            return {"sent": False, "dry_run": True, "message": text}

        payload: dict[str, Any] = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        if self.webhook_url:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
            return {"sent": True, "dry_run": False, "via": "webhook"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"channel": self.channel, "text": text, "blocks": blocks},
            )
            data = resp.json()
            if not data.get("ok"):
                logger.warning("slack_post_failed", extra={"error": data.get("error")})
                return {"sent": False, "dry_run": False, "error": data.get("error")}
        return {"sent": True, "dry_run": False, "via": "bot"}

    async def notify_approval_needed(
        self,
        experiment_id: str,
        name: str,
        environment: str,
        *,
        api_base: str = "http://127.0.0.1:8000",
    ) -> dict[str, Any]:
        text = (
            f":warning: *Chaos experiment awaiting approval*\n"
            f"*{name}* (`{experiment_id}`)\n"
            f"Environment: `{environment}`\n"
            f"Approve via API: `POST {api_base}/experiments/{experiment_id}/approve`"
        )
        return await self.post_message(text)

    async def notify_slo_breach(self, experiment_id: str, reason: str) -> dict[str, Any]:
        text = f":rotating_light: *SLO breach* on `{experiment_id}`\n{reason}"
        return await self.post_message(text)

    async def notify_campaign_complete(self, campaign_id: str, name: str, leader: str) -> dict[str, Any]:
        text = f":trophy: *Red/Blue campaign complete* — {name} (`{campaign_id}`)\nLeader: *{leader}*"
        return await self.post_message(text)
