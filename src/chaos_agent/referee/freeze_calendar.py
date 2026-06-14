"""Freeze calendar — blackout windows for chaos experiments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from chaos_agent.config import get_settings


@dataclass(frozen=True)
class FreezeWindow:
    name: str
    weekday: Optional[int] = None  # 0=Monday, 5=Saturday, 6=Sunday
    hour_start: int = 0
    hour_end: int = 24
    enforced: bool = True


DEFAULT_FREEZE_WINDOWS = [
    FreezeWindow(name="weekend-blackout", weekday=5, hour_start=0, hour_end=24, enforced=True),
    FreezeWindow(name="weekend-blackout", weekday=6, hour_start=0, hour_end=24, enforced=True),
    FreezeWindow(name="business-hours-advisory", weekday=0, hour_start=9, hour_end=17, enforced=False),
    FreezeWindow(name="business-hours-advisory", weekday=1, hour_start=9, hour_end=17, enforced=False),
    FreezeWindow(name="business-hours-advisory", weekday=2, hour_start=9, hour_end=17, enforced=False),
    FreezeWindow(name="business-hours-advisory", weekday=3, hour_start=9, hour_end=17, enforced=False),
    FreezeWindow(name="business-hours-advisory", weekday=4, hour_start=9, hour_end=17, enforced=False),
]


def get_freeze_windows() -> list[dict[str, Any]]:
    ts = datetime.now(timezone.utc)
    weekday = ts.weekday()
    out = []
    for w in DEFAULT_FREEZE_WINDOWS:
        active = w.weekday == weekday and w.enforced
        if w.weekday == weekday:
            if w.hour_start <= ts.hour < w.hour_end:
                next_status = "Active now" if w.enforced else "Advisory now"
            else:
                next_status = "Not in window"
        elif w.weekday is not None:
            next_status = f"Next {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][w.weekday]}"
        else:
            next_status = "Manual"
        out.append(
            {
                "label": w.name,
                "schedule": f"weekday={w.weekday} hours {w.hour_start}-{w.hour_end} UTC",
                "next": next_status,
                "enforced": w.enforced,
                "active": active,
            },
        )
    return out


def active_freeze_reason(
    now: Optional[datetime] = None,
    *,
    enforce_freeze: Optional[bool] = None,
) -> Optional[str]:
    settings = get_settings()
    if enforce_freeze is None:
        enforce_freeze = settings.enforce_freeze_calendar

    if not enforce_freeze:
        return None

    ts = now or datetime.now(timezone.utc)
    weekday = ts.weekday()
    hour = ts.hour

    for w in DEFAULT_FREEZE_WINDOWS:
        if not w.enforced or w.weekday is None:
            continue
        if w.weekday == weekday and w.hour_start <= hour < w.hour_end:
            return f"{w.name} — experiments blocked until window ends"

    return None
