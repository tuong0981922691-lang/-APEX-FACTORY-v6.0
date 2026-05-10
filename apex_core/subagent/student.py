"""Student Subagent — 3-tier analysis (NT24 §4 Sinh viên metaphor).

Tiers:
  - Surface: skim file once (~30s), summarize in 1 paragraph
  - Mid: analyze code (~3 min), find 3 risks
  - Deep: prove/disprove hypothesis (~10 min), cite specific evidence
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AnalysisResult:
    tier: str
    file_path: str
    summary: str
    risks: list[str]
    evidence: list[str]


def surface(file_path: str) -> AnalysisResult:
    """Tier 1: Skim file, produce 1-paragraph summary."""
    path = Path(file_path)
    if not path.exists():
        return AnalysisResult(
            tier="surface",
            file_path=file_path,
            summary=f"File not found: {file_path}",
            risks=["FILE_NOT_FOUND"],
            evidence=[],
        )
    content = path.read_text(errors="replace")
    line_count = len(content.splitlines())
    return AnalysisResult(
        tier="surface",
        file_path=file_path,
        summary=f"File has {line_count} lines. First 100 chars: {content[:100]}",
        risks=[],
        evidence=[f"line_count={line_count}"],
    )


def mid(file_path: str, hypothesis: str = "") -> AnalysisResult:
    """Tier 2: Analyze code, find 3 risks."""
    path = Path(file_path)
    if not path.exists():
        return AnalysisResult(
            tier="mid",
            file_path=file_path,
            summary=f"File not found: {file_path}",
            risks=["FILE_NOT_FOUND"],
            evidence=[],
        )
    content = path.read_text(errors="replace")
    risks = []
    if "TODO" in content:
        risks.append("Contains TODO markers")
    if "pass" in content and "# " not in content.split("pass")[0][-20:]:
        risks.append("Empty pass statements detected")
    if len(content.splitlines()) > 500:
        risks.append("Large file (>500 lines) — consider splitting")
    return AnalysisResult(
        tier="mid",
        file_path=file_path,
        summary=f"Analysis for hypothesis: '{hypothesis}'. Found {len(risks)} risks.",
        risks=risks[:3],
        evidence=[f"file_size={len(content)}", f"lines={len(content.splitlines())}"],
    )


def deep(file_path: str, hypothesis: str, evidence_required: str = "") -> AnalysisResult:
    """Tier 3: Prove/disprove hypothesis with specific citations."""
    path = Path(file_path)
    if not path.exists():
        return AnalysisResult(
            tier="deep",
            file_path=file_path,
            summary="Cannot verify: file not found",
            risks=["VERIFICATION_IMPOSSIBLE"],
            evidence=[],
        )
    content = path.read_text(errors="replace")
    lines = content.splitlines()
    evidence = []
    for i, line in enumerate(lines, 1):
        if hypothesis.lower() in line.lower():
            evidence.append(f"Line {i}: {line.strip()[:100]}")
    proved = len(evidence) > 0
    return AnalysisResult(
        tier="deep",
        file_path=file_path,
        summary=f"Hypothesis '{hypothesis}': {'PROVED' if proved else 'DISPROVED'}. {len(evidence)} citations found.",
        risks=[] if proved else [f"Hypothesis not supported: {hypothesis}"],
        evidence=evidence[:10],
    )
