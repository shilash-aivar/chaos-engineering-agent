"""Wasm plugin types."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PluginResult(BaseModel):
    passed: bool
    message: str = ""
    plugin: str
    runtime: str = "python"  # wasm | python
    details: dict = Field(default_factory=dict)
