"""Per-request context stored on request.state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RequestContext:
    request_id: str
    authenticated: bool = False
    auth_method: Optional[str] = None
    audit_notes: list[str] = field(default_factory=list)
