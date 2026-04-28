"""Minimal principle enforcement compatibility module."""
from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar


class Principle(str, Enum):
    HUMAN_SUPREMACY = "NT5"
    AUDITABILITY = "NT8"
    DESIGN_SYSTEM_CONSISTENCY = "NT11"
    ACCESSIBILITY = "NT12"


F = TypeVar("F", bound=Callable[..., Any])


def enforce_principle(_principle: Principle) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper  # type: ignore[return-value]
    return decorator


__all__ = ["Principle", "enforce_principle"]
