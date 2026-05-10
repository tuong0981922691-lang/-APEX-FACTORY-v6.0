"""Cross-AI Diff Probe (NT20-08 / C10).

Same input → AI1 → AI2 → AI1 again. Diff > 30% = flag.
"""


def calculate_diff(response_a: str, response_b: str) -> float:
    """Calculate word-level diff between two responses."""
    words_a = set(response_a.lower().split())
    words_b = set(response_b.lower().split())
    if not words_a and not words_b:
        return 0.0
    union = words_a | words_b
    intersection = words_a & words_b
    return round(1.0 - (len(intersection) / len(union)), 4) if union else 0.0


def run_cross_ai_probe(input_text: str, response_ai1_v1: str, response_ai2: str, response_ai1_v2: str) -> dict:
    """Run the full cross-AI probe: AI1 → AI2 → AI1.

    Flag if diff between AI1 v1 and AI1 v2 > 30% (self-consistency check).
    Also check AI1 vs AI2 difference.
    """
    diff_self = calculate_diff(response_ai1_v1, response_ai1_v2)
    diff_cross = calculate_diff(response_ai1_v1, response_ai2)

    return {
        "input_preview": input_text[:100],
        "diff_ai1_self": diff_self,
        "diff_ai1_vs_ai2": diff_cross,
        "self_flagged": diff_self > 0.30,
        "cross_flagged": diff_cross > 0.50,
        "threshold_self": 0.30,
        "threshold_cross": 0.50,
    }
