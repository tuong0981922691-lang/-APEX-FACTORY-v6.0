"""Decision Brain — Bạch Tuộc não trung tâm (NT23).

7 input tentacles → 1 central brain → multiple output gates.
"""
from datetime import datetime, timezone

from pydantic import BaseModel


class InputSource(BaseModel):
    source_type: str  # customer_chat | customer_upload | ai_crawl | ai_premium | repo_mining | owner_paste | voice
    content: str
    metadata: dict = {}
    received_at: str = ""


class Decision(BaseModel):
    decision_id: str
    inputs_used: list[str]
    draft: str
    confidence: float
    requires_approval: bool = True
    created_at: str = ""


INPUT_TENTACLES = [
    "customer_chat",
    "customer_upload",
    "customer_voice",
    "ai_free_crawl",
    "ai_premium_dump",
    "repo_mining",
    "owner_direct_paste",
]


def synthesize_inputs(inputs: list[InputSource]) -> Decision:
    """Synthesize multiple input sources into a single decision draft."""
    combined = "\n".join(f"[{inp.source_type}] {inp.content}" for inp in inputs)
    return Decision(
        decision_id=f"dec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        inputs_used=[inp.source_type for inp in inputs],
        draft=combined[:2000],
        confidence=min(len(inputs) / 3.0, 1.0),
        requires_approval=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
