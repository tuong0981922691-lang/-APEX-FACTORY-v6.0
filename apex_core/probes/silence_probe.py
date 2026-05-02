"""Silence-Period Probe (NT20-10 / C9).

Save AI output → wait 60 min → ask same question → compare.
Drift > 20% = flag.
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def save_response(probe_id: str, response: str, data_root: Path, version: int = 1) -> Path:
    """Save AI response for later comparison."""
    silence_dir = data_root / "silence"
    silence_dir.mkdir(parents=True, exist_ok=True)
    output_file = silence_dir / f"{probe_id}_v{version}.json"
    output_file.write_text(json.dumps({
        "probe_id": probe_id,
        "version": version,
        "response": response,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2))
    return output_file


def compare_responses(probe_id: str, data_root: Path) -> dict:
    """Compare v1 and v2 responses. Return drift score."""
    silence_dir = data_root / "silence"
    v1_file = silence_dir / f"{probe_id}_v1.json"
    v2_file = silence_dir / f"{probe_id}_v2.json"

    if not v1_file.exists() or not v2_file.exists():
        return {"probe_id": probe_id, "error": "Missing version file", "drift": None}

    v1 = json.loads(v1_file.read_text())
    v2 = json.loads(v2_file.read_text())

    r1 = set(v1["response"].lower().split())
    r2 = set(v2["response"].lower().split())

    if not r1:
        return {"probe_id": probe_id, "drift": 1.0, "flagged": True}

    intersection = r1 & r2
    union = r1 | r2
    jaccard = len(intersection) / len(union) if union else 1.0
    drift = 1.0 - jaccard

    return {
        "probe_id": probe_id,
        "drift": round(drift, 4),
        "flagged": drift > 0.20,
        "threshold": 0.20,
    }
