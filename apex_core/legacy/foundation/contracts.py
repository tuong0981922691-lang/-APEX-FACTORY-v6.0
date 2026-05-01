"""
APEX Factory v5.0 Legacy - Contracts
Preserved from v5.0 for backward compatibility.

Core state machine contracts for brains.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum


class BrainState(str, Enum):
    """State machine for brain lifecycle."""
    IDLE = "IDLE"
    INGESTING = "INGESTING"
    PROCESSING = "PROCESSING"
    EVALUATING = "EVALUATING"
    EMITTING = "EMITTING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    SUSPENDED = "SUSPENDED"


def now_utc_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "BrainState",
    "now_utc_iso",
]
