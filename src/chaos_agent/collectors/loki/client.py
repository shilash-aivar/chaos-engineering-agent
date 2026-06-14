"""Loki HTTP client — LogQL range queries."""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Optional

import httpx

from chaos_agent.config import get_settings

logger = logging.getLogger(__name__)


class LokiClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or get_settings().loki_url).rstrip("/")

    async def query_range(
        self,
        logql: str,
        start: datetime,
        end: datetime,
        *,
        limit: int = 200,
    ) -> list[str]:
        """Return log lines in the given time window."""
        url = f"{self.base_url}/loki/api/v1/query_range"
        params = {
            "query": logql,
            "start": str(int(start.timestamp() * 1e9)),
            "end": str(int(end.timestamp() * 1e9)),
            "limit": str(limit),
            "direction": "backward",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except Exception as exc:
            logger.warning("loki_query_failed", extra={"error": str(exc), "query": logql})
            return []

        if payload.get("status") != "success":
            return []

        lines: list[str] = []
        for stream in payload.get("data", {}).get("result", []):
            for _ts, line in stream.get("values", []):
                if line:
                    lines.append(line)
        return lines

    @staticmethod
    def summarize_lines(lines: list[str], *, max_patterns: int = 3, max_samples: int = 5) -> tuple[int, list[str], list[str]]:
        error_lines = [ln for ln in lines if re.search(r"error|exception|fail|timeout|refused", ln, re.I)]
        patterns: Counter[str] = Counter()
        for ln in error_lines:
            normalized = re.sub(r"\d+", "N", ln[:120])
            patterns[normalized] += 1
        top_patterns = [p for p, _ in patterns.most_common(max_patterns)]
        samples = error_lines[:max_samples] if error_lines else lines[:max_samples]
        return len(error_lines), top_patterns, samples

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/ready")
                return response.status_code == 200
        except Exception:
            return False
