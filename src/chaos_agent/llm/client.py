"""Anthropic client for structured agent outputs."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from chaos_agent.config import get_settings

logger = logging.getLogger(__name__)

_JSON_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


class LLMClient:
    """Thin async wrapper around the Anthropic Messages API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self._client: Any = None

    @property
    def available(self) -> bool:
        return bool(self.api_key.strip())

    def _get_client(self) -> Any:
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 4096,
    ) -> Optional[dict[str, Any]]:
        """Return parsed JSON object or None when LLM unavailable / parse fails."""
        if not self.available:
            return None
        try:
            client = self._get_client()
            message = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(
                block.text for block in message.content if getattr(block, "type", "") == "text"
            )
            return _parse_json_object(text)
        except Exception as exc:
            logger.warning("llm_complete_failed", extra={"error": str(exc)})
            return None


def _parse_json_object(text: str) -> Optional[dict[str, Any]]:
    stripped = text.strip()
    match = _JSON_BLOCK.search(stripped)
    candidate = match.group(1).strip() if match else stripped
    try:
        data = json.loads(candidate)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(candidate[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
    return None


_llm: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm
