"""
APEX Factory v5.0 Legacy - Brain Base
Preserved from v5.0 for backward compatibility.

Base class for all brain implementations.
"""
from __future__ import annotations

import functools
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from apex_core.legacy.foundation.contracts import BrainState, now_utc_iso


@dataclass
class BrainContext:
    """Context passed to brains during processing."""
    session_id: str = ""
    trace_id: str = ""
    run_id: str = ""
    current_date: str = ""
    draws: List[Any] = field(default_factory=list)
    current_idx: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_brain: Optional[str] = None
    timestamp: str = field(default_factory=now_utc_iso)


@dataclass
class BrainResult:
    """Result from brain processing."""
    brain_name: str = ""
    brain_id: str = ""
    state: BrainState = BrainState.IDLE
    success: bool = False
    output: Any = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=now_utc_iso)


class BrainLifecycleHooks:
    """Hooks for brain lifecycle events."""

    def on_start(self, brain_name: str, context: BrainContext) -> None:
        pass

    def on_complete(self, brain_name: str, result: BrainResult) -> None:
        pass

    def on_error(self, brain_name: str, error: Exception) -> None:
        pass

    def on_state_change(self, brain_name: str, old: BrainState, new: BrainState) -> None:
        pass


class NoOpHooks(BrainLifecycleHooks):
    """No-op implementation of lifecycle hooks."""
    pass


class BaseBrain:
    """Abstract base class for all brain implementations."""

    def __init__(self, name: Optional[str] = None, hooks: Optional[BrainLifecycleHooks] = None):
        self._name = name or getattr(self, 'BRAIN_NAME', self.__class__.__name__)
        self._hooks = hooks or NoOpHooks()
        self._state = BrainState.IDLE

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> BrainState:
        return self._state

    def _transition(self, new_state: BrainState) -> None:
        old = self._state
        self._state = new_state
        self._hooks.on_state_change(self._name, old, new_state)

    def validate_inputs(self, context: BrainContext) -> List[str]:
        """Override in subclass to check required inputs."""
        return []

    def process(self, context: BrainContext, **kwargs: Any) -> BrainResult:
        """Process input and return result. Override in subclass."""
        return BrainResult(brain_name=self._name, state=BrainState.COMPLETE)

    def execute(self, context: BrainContext) -> BrainResult:
        """Execute the brain logic. Override in subclass (v6 pattern)."""
        return self.process(context)

    def run(self, context: BrainContext) -> BrainResult:
        """Run the brain with lifecycle hooks."""
        self._hooks.on_start(self._name, context)
        self._transition(BrainState.PROCESSING)
        try:
            missing = self.validate_inputs(context)
            if missing:
                result = BrainResult(
                    brain_name=self._name,
                    state=BrainState.ERROR,
                    errors=[f"Missing input: {m}" for m in missing],
                )
                self._transition(BrainState.ERROR)
                return result

            result = self.execute(context)
            self._transition(BrainState.COMPLETE)
            self._hooks.on_complete(self._name, result)
            return result
        except Exception as e:
            self._transition(BrainState.ERROR)
            self._hooks.on_error(self._name, e)
            return BrainResult(
                brain_name=self._name,
                state=BrainState.ERROR,
                errors=[str(e)],
            )

    def reset(self) -> None:
        self._state = BrainState.IDLE


def time_it(func: Callable) -> Callable:
    """Decorator that measures function execution time."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        if hasattr(result, 'metadata') and isinstance(result.metadata, dict):
            result.metadata['elapsed_ms'] = round(elapsed * 1000, 2)
        return result
    return wrapper


__all__ = [
    "BaseBrain",
    "BrainContext",
    "BrainLifecycleHooks",
    "BrainResult",
    "NoOpHooks",
    "time_it",
]
