"""Round Table 7-day vote (NT19 §8).

Every Tuesday 09:00 UTC+7:
  - Read data/radar/*.jsonl (7 days)
  - Read reports/C2_pytest_*.txt (7 days)
  - 14 brains (B1-B14) vote each AI free → score 0-100
  - Score < 60 → kill recommendation
  - Output: data/round_table/round_<N>.json + Telegram notify Owner
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class VoteResult(BaseModel):
    ai_id: str
    scores: dict[str, int]  # brain_id → score
    average: float
    recommendation: str  # "keep" or "kill"


class RoundTableSession(BaseModel):
    round_number: int
    date: str
    votes: list[VoteResult]
    override: Optional[str] = None  # Owner override if any


KILL_THRESHOLD = 60


def calculate_vote(ai_id: str, brain_scores: dict[str, int]) -> VoteResult:
    """Calculate vote result for a single AI."""
    avg = sum(brain_scores.values()) / len(brain_scores) if brain_scores else 0
    recommendation = "keep" if avg >= KILL_THRESHOLD else "kill"
    return VoteResult(
        ai_id=ai_id,
        scores=brain_scores,
        average=round(avg, 2),
        recommendation=recommendation,
    )


def run_round_table(round_number: int, ai_scores: dict[str, dict[str, int]]) -> RoundTableSession:
    """Run a complete round table session."""
    votes = [calculate_vote(ai_id, scores) for ai_id, scores in ai_scores.items()]
    return RoundTableSession(
        round_number=round_number,
        date=datetime.now(timezone.utc).isoformat(),
        votes=votes,
    )


def save_result(session: RoundTableSession, data_root: Path) -> Path:
    """Save round table result to disk."""
    rt_dir = data_root / "round_table"
    rt_dir.mkdir(parents=True, exist_ok=True)
    output_file = rt_dir / f"round_{session.round_number}.json"
    output_file.write_text(session.model_dump_json(indent=2))
    return output_file
