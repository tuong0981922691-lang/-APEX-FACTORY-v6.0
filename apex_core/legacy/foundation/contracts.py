"""Shared legacy contracts used by the runnable scaffold."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum


class BrainState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["BrainState", "now_utc_iso"]
