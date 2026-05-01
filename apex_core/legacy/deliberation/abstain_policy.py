"""
APEX Factory v5.0 Legacy - Abstain Policy Engine
Preserved from v5.0 for backward compatibility.

Implements the policy for when the system should abstain from acting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AbstainReason(str, Enum):
    """Reasons why the system may abstain."""
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    VIOLATES_PRINCIPLE = "VIOLATES_PRINCIPLE"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_MISSING = "TOKEN_MISSING"
    SCOPE_INSUFFICIENT = "SCOPE_INSUFFICIENT"
    HUMAN_OVERRIDE_REQUIRED = "HUMAN_OVERRIDE_REQUIRED"
    QUALITY_THRESHOLD_NOT_MET = "QUALITY_THRESHOLD_NOT_MET"
    DOMAIN_UNSUPPORTED = "DOMAIN_UNSUPPORTED"


@dataclass
class AbstainDecision:
    should_abstain: bool
    reasons: List[AbstainReason] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AbstainPolicyEngine:
    """Engine that evaluates whether the system should abstain from an action."""

    def __init__(self, confidence_threshold: float = 0.7):
        self._confidence_threshold = confidence_threshold
        self._kill_switch_active = False

    def evaluate(
        self,
        confidence: float = 1.0,
        has_token: bool = True,
        token_valid: bool = True,
        quality_score: Optional[float] = None,
    ) -> AbstainDecision:
        reasons: List[AbstainReason] = []

        if self._kill_switch_active:
            reasons.append(AbstainReason.KILL_SWITCH_ACTIVE)

        if confidence < self._confidence_threshold:
            reasons.append(AbstainReason.CONFIDENCE_TOO_LOW)

        if not has_token:
            reasons.append(AbstainReason.TOKEN_MISSING)
        elif not token_valid:
            reasons.append(AbstainReason.TOKEN_EXPIRED)

        if quality_score is not None and quality_score < self._confidence_threshold:
            reasons.append(AbstainReason.QUALITY_THRESHOLD_NOT_MET)

        return AbstainDecision(
            should_abstain=len(reasons) > 0,
            reasons=reasons,
        )

    def set_kill_switch(self, active: bool) -> None:
        self._kill_switch_active = active


__all__ = [
    "AbstainPolicyEngine",
    "AbstainReason",
    "AbstainDecision",
]
