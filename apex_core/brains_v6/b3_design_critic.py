"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: b3_design_critic.py

Vai trò B3: DESIGN CRITIC (PRE-SYNTHESIS)
    Chạy TRƯỚC khi B4 build DesignGraph. Nhiệm vụ: soi brief + slot_plan
    để bắt các mầm mống lỗi TRƯỚC khi lãng phí cycle tổng hợp.

    Khác với Round Table Deliberation (Phase 2) chạy SAU synthesis, B3
    là kiểm lâm tiền tuyến - nhẹ, nhanh, không LLM.

7 heuristics áp dụng tại đây (thay thế 3 detector xổ số cũ):
    H1 - TONE_COHERENCE       : tone set không mâu thuẫn
    H2 - FEATURE_COHERENCE    : feature ăn với product_type
    H3 - BUNDLE_REALISM       : ngân sách bundle khớp số feature
    H4 - A11Y_FEASIBILITY     : WCAG target khớp color preference thô
    H5 - REFERENCE_HEALTH     : URL format & không tự-tham-chiếu
    H6 - CRITICAL_COMPLETENESS: feature critical không thiếu
    H7 - SCOPE_CREEP          : feature count không vượt ngưỡng sanity

Output: CritiqueReport với severity (error/warning/info) + suggestion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from apex_core.brains_v6.b2_component_scout import PRODUCT_DEFAULT_FEATURES
from apex_core.brains_v6.brain_base_v6 import (
    BrainStage,
    FactoryBrain,
    FactoryBrainContext,
    FactoryBrainResult,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)

# ============================================================
# 0. VERSION
# ============================================================

B3_VERSION = "6.0.0"


# ============================================================
# 1. CRITIQUE SEVERITY + FINDING
# ============================================================

class CritiqueSeverity(str, Enum):
    ERROR = "error"             # Block synthesis
    WARNING = "warning"         # Cho synthesize nhưng bị Radar 4D trừ điểm
    INFO = "info"               # Chỉ audit, không ảnh hưởng quyết định


@dataclass(frozen=True)
class CritiqueFinding:
    heuristic_id: str
    title: str
    severity: CritiqueSeverity
    message: str
    affected: Tuple[str, ...] = ()
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "heuristic_id": self.heuristic_id,
            "title": self.title,
            "severity": self.severity.value,
            "message": self.message,
            "affected": list(self.affected),
            "suggestion": self.suggestion,
        }


# ============================================================
# 2. TONE CONFLICT MATRIX
# ============================================================

# Các cặp tone xung đột mạnh (áp dụng bất kể ngữ cảnh)
TONE_HARD_CONFLICTS: Tuple[Tuple[str, str], ...] = (
    ("minimal", "bold"),
    ("minimal", "playful"),
    ("luxury", "playful"),
    ("corporate", "playful"),
    ("editorial", "tech"),
)

# Tone tương thích cao (info-level boost nếu đi cùng)
TONE_SOFT_AFFINITY: Tuple[Tuple[str, str], ...] = (
    ("minimal", "editorial"),
    ("minimal", "tech"),
    ("luxury", "editorial"),
    ("luxury", "warm"),
    ("corporate", "tech"),
    ("playful", "warm"),
    ("playful", "bold"),
)


# ============================================================
# 3. FEATURE / PRODUCT COHERENCE MAP
# ============================================================

# Feature "lạ" với product_type - không block nhưng warn
UNUSUAL_FEATURES_FOR_PRODUCT: Dict[str, FrozenSet[str]] = {
    "landing_page": frozenset({"cart", "checkout", "product_grid"}),
    "blog": frozenset({"cart", "checkout", "pricing_table"}),
    "portfolio": frozenset({"cart", "checkout", "pricing_table"}),
    "dashboard": frozenset({"hero", "testimonials"}),
    "ecommerce": frozenset({}),     # ecommerce cho phép gần hết
    "saas_app": frozenset({"cart", "checkout"}),
}


# Ngưỡng bundle KB ước tính theo feature (rất thô)
FEATURE_ESTIMATED_KB: Dict[str, float] = {
    "navbar": 8,
    "hero": 15,
    "cta": 3,
    "pricing_table": 12,
    "testimonials": 10,
    "faq": 8,
    "contact_form": 15,        # form validation nhẹ
    "footer": 6,
    "auth": 25,                # JWT/session
    "search": 20,              # fuzzy match
    "dark_mode": 4,
    "product_grid": 30,
    "cart": 25,
    "checkout": 35,
    "blog_list": 15,
    "animation": 18,           # framer-motion-ish
    "multi_language": 22,
    "sidebar": 10,
    "data_table": 35,
}

BASELINE_BUNDLE_KB = 45        # React + shell cơ bản
REASONABLE_FEATURE_COUNT_BY_PRODUCT: Dict[str, Tuple[int, int]] = {
    "landing_page": (3, 9),
    "dashboard": (5, 15),
    "ecommerce": (6, 14),
    "blog": (3, 8),
    "portfolio": (3, 7),
    "saas_app": (5, 12),
}
DEFAULT_REASONABLE_FEATURE_RANGE: Tuple[int, int] = (2, 12)


# ============================================================
# 4. HEURISTICS
# ============================================================

class HeuristicBase:
    HEURISTIC_ID: str = "H0"
    TITLE: str = "Base"

    @enforce_principle_v6(PrincipleV6.NT7_MICRO_PHENOMENA)
    def check(self, context: FactoryBrainContext) -> List[CritiqueFinding]:
        raise NotImplementedError

    @classmethod
    def _finding(
        cls,
        severity: CritiqueSeverity,
        message: str,
        affected: Tuple[str, ...] = (),
        suggestion: str = "",
    ) -> CritiqueFinding:
        return CritiqueFinding(
            heuristic_id=cls.HEURISTIC_ID,
            title=cls.TITLE,
            severity=severity,
            message=message,
            affected=affected,
            suggestion=suggestion,
        )


class H1_ToneCoherence(HeuristicBase):
    HEURISTIC_ID = "H1"
    TITLE = "Tone Coherence"

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()
        tone = set(brief.tone)

        if len(tone) == 0:
            findings.append(self._finding(
                CritiqueSeverity.INFO,
                "Brief không khai báo tone - B4 sẽ dùng tone mặc định 'minimal'.",
                suggestion="Thêm tone vào brief để B4 chọn palette phù hợp.",
            ))
            return findings

        if len(tone) > 3:
            findings.append(self._finding(
                CritiqueSeverity.WARNING,
                f"Khai báo {len(tone)} tone ({sorted(tone)}) - nhiều hơn ngưỡng 3.",
                affected=tuple(sorted(tone)),
                suggestion="Rút về 2-3 tone chủ đạo để visual không rối.",
            ))

        for a, b in TONE_HARD_CONFLICTS:
            if a in tone and b in tone:
                findings.append(self._finding(
                    CritiqueSeverity.ERROR,
                    f"Tone xung đột: '{a}' và '{b}' không thể cùng tồn tại.",
                    affected=(a, b),
                    suggestion="Chọn 1 trong 2, hoặc thêm context phân vùng.",
                ))

        return findings


class H2_FeatureCoherence(HeuristicBase):
    HEURISTIC_ID = "H2"
    TITLE = "Feature × ProductType Coherence"

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()
        features = set(brief.features)
        unusual = UNUSUAL_FEATURES_FOR_PRODUCT.get(brief.product_type, frozenset())

        for feat in features:
            if feat in unusual:
                findings.append(self._finding(
                    CritiqueSeverity.WARNING,
                    f"Feature '{feat}' không điển hình cho {brief.product_type}.",
                    affected=(feat,),
                    suggestion=(
                        f"Xem xét: có thực sự cần '{feat}' cho "
                        f"{brief.product_type} không?"
                    ),
                ))

        return findings


class H3_BundleRealism(HeuristicBase):
    HEURISTIC_ID = "H3"
    TITLE = "Bundle Budget Realism"

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()
        max_kb = brief.constraints.get("max_bundle_kb")
        if max_kb is None:
            return findings

        # Ước tính tối thiểu
        estimated = BASELINE_BUNDLE_KB + sum(
            FEATURE_ESTIMATED_KB.get(f, 10) for f in brief.features
        )

        if max_kb < BASELINE_BUNDLE_KB:
            findings.append(self._finding(
                CritiqueSeverity.ERROR,
                f"Bundle budget {max_kb}kb < baseline React {BASELINE_BUNDLE_KB}kb - bất khả thi.",
                suggestion=f"Nâng budget lên tối thiểu {BASELINE_BUNDLE_KB + 20}kb hoặc dùng HTML static.",
            ))
        elif estimated > max_kb * 1.25:
            findings.append(self._finding(
                CritiqueSeverity.ERROR,
                f"Bundle ước tính {estimated:.0f}kb > ngân sách {max_kb}kb × 1.25.",
                affected=tuple(brief.features),
                suggestion=(
                    f"Cắt giảm feature hoặc dùng code-splitting. "
                    f"Giới hạn hiện tại khả thi cho ~{int((max_kb - BASELINE_BUNDLE_KB) / 10)} feature."
                ),
            ))
        elif estimated > max_kb:
            findings.append(self._finding(
                CritiqueSeverity.WARNING,
                f"Bundle ước tính {estimated:.0f}kb > budget {max_kb}kb (dư ~{estimated - max_kb:.0f}kb).",
                suggestion="Cân nhắc lazy-load các feature không critical.",
            ))
        return findings


class H4_A11yFeasibility(HeuristicBase):
    HEURISTIC_ID = "H4"
    TITLE = "A11y Feasibility"

    # Cặp (bg, fg) có vấn đề contrast kinh điển
    LOW_CONTRAST_PAIRS: Tuple[Tuple[str, str], ...] = (
        ("yellow", "white"),
        ("yellow", "pastel"),
        ("pastel", "white"),
        ("gray", "white"),
        ("pastel", "pastel"),
    )

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()

        wcag_level = brief.constraints.get("wcag_level", "").upper()
        colors = set(c.lower() for c in brief.color_preferences)

        if wcag_level == "AAA" and colors:
            findings.append(self._finding(
                CritiqueSeverity.INFO,
                "WCAG AAA yêu cầu contrast 7.0 - rất khó với color preference tự do.",
                suggestion="B4 sẽ bắt buộc chọn biến thể đậm từ palette.",
            ))

        # Cảnh báo cặp màu low-contrast
        for a, b in self.LOW_CONTRAST_PAIRS:
            if a in colors and b in colors:
                findings.append(self._finding(
                    CritiqueSeverity.WARNING,
                    f"Cặp màu {a!r} + {b!r} có nguy cơ contrast < 4.5 (WCAG AA).",
                    affected=(a, b),
                    suggestion="Cần màu đậm hơn cho text hoặc bg tối cho {a} text.",
                ))

        if brief.constraints.get("dark_mode_required") and not colors:
            findings.append(self._finding(
                CritiqueSeverity.INFO,
                "Dark mode được yêu cầu nhưng không khai báo màu - B4 dùng palette mặc định.",
            ))

        return findings


class H5_ReferenceHealth(HeuristicBase):
    HEURISTIC_ID = "H5"
    TITLE = "Reference Health"

    URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()

        for ref in brief.references:
            if not self.URL_PATTERN.match(ref):
                findings.append(self._finding(
                    CritiqueSeverity.WARNING,
                    f"Reference không đúng format URL: {ref!r}",
                    affected=(ref,),
                    suggestion="Loại bỏ hoặc sửa format.",
                ))
                continue
            # Tránh self-reference
            if "apex-factory" in ref.lower() or "apex_factory" in ref.lower():
                findings.append(self._finding(
                    CritiqueSeverity.WARNING,
                    f"Reference tự tham chiếu: {ref}",
                    affected=(ref,),
                ))

        if len(brief.references) > 10:
            findings.append(self._finding(
                CritiqueSeverity.WARNING,
                f"Quá nhiều reference ({len(brief.references)} > 10) - B4 có thể confused.",
                suggestion="Giữ 3-5 reference chất lượng cao nhất.",
            ))

        return findings


class H6_CriticalCompleteness(HeuristicBase):
    HEURISTIC_ID = "H6"
    TITLE = "Critical Feature Completeness"

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()
        slot_plan = context.shared_memory.get("slot_plan", {})

        # Đọc từ SlotPlan (do B2 đã chạy)
        missing = slot_plan.get("missing_critical_features", [])
        if missing:
            findings.append(self._finding(
                CritiqueSeverity.ERROR,
                f"Thiếu {len(missing)} feature critical: {missing}",
                affected=tuple(missing),
                suggestion=(
                    "B6 phải dùng Borrowing Protocol để sinh component "
                    "hoặc C2 cần bổ sung catalog."
                ),
            ))

        # Kiểm thêm theo product default
        expected = set(PRODUCT_DEFAULT_FEATURES.get(brief.product_type, ()))
        declared = set(brief.features)
        gap = expected - declared
        if gap:
            findings.append(self._finding(
                CritiqueSeverity.INFO,
                f"Brief thiếu {len(gap)} feature mặc định của {brief.product_type}: {sorted(gap)}",
                affected=tuple(sorted(gap)),
                suggestion="B4 sẽ tự bổ sung từ PRODUCT_DEFAULT_FEATURES.",
            ))

        return findings


class H7_ScopeCreep(HeuristicBase):
    HEURISTIC_ID = "H7"
    TITLE = "Scope Creep"

    def check(self, context):
        findings: List[CritiqueFinding] = []
        brief = context.require_brief()
        count = len(brief.features)

        lo, hi = REASONABLE_FEATURE_COUNT_BY_PRODUCT.get(
            brief.product_type, DEFAULT_REASONABLE_FEATURE_RANGE
        )

        if count > hi:
            findings.append(self._finding(
                CritiqueSeverity.WARNING,
                f"Feature count {count} > ngưỡng cao {hi} cho {brief.product_type}.",
                suggestion=(
                    "Scope quá rộng có thể kéo dài time-to-build và phá focus. "
                    "Chia pha v1/v2."
                ),
            ))
        elif count < lo and count > 0:
            findings.append(self._finding(
                CritiqueSeverity.INFO,
                f"Feature count {count} < ngưỡng thấp {lo} - product có thể quá đơn sơ.",
            ))

        return findings


# ============================================================
# 5. CRITIQUE REPORT
# ============================================================

@dataclass
class CritiqueReport:
    brief_id: str
    findings: List[CritiqueFinding] = field(default_factory=list)
    heuristics_run: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == CritiqueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == CritiqueSeverity.WARNING)

    @property
    def is_blocking(self) -> bool:
        """Có ít nhất 1 ERROR → block B4."""
        return self.error_count > 0

    def health_score(self) -> float:
        """0..1. 1.0 = hoàn hảo, 0.0 = toàn error."""
        if not self.findings:
            return 1.0
        penalty = 0.0
        for f in self.findings:
            penalty += {
                CritiqueSeverity.ERROR: 0.25,
                CritiqueSeverity.WARNING: 0.08,
                CritiqueSeverity.INFO: 0.0,
            }[f.severity]
        return round(max(0.0, 1.0 - penalty), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "heuristics_run": self.heuristics_run,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": sum(1 for f in self.findings if f.severity == CritiqueSeverity.INFO),
            "is_blocking": self.is_blocking,
            "health_score": self.health_score(),
            "findings": [f.to_dict() for f in self.findings],
        }


# ============================================================
# 6. B3 DESIGN CRITIC BRAIN
# ============================================================

class B3DesignCritic(FactoryBrain):
    BRAIN_ID = "B3_v6"
    BRAIN_NAME = "DesignCritic"
    BRAIN_STAGE = BrainStage.CRITIQUE_PRE
    REQUIRED_CONTEXT_ATTRS = ("brief_spec",)

    def __init__(
        self,
        hooks=None,
        heuristics: Optional[List[HeuristicBase]] = None,
    ):
        super().__init__(hooks=hooks)
        self._heuristics: List[HeuristicBase] = heuristics or [
            H1_ToneCoherence(),
            H2_FeatureCoherence(),
            H3_BundleRealism(),
            H4_A11yFeasibility(),
            H5_ReferenceHealth(),
            H6_CriticalCompleteness(),
            H7_ScopeCreep(),
        ]

    def add_heuristic(self, h: HeuristicBase) -> None:
        """NT10 hot-plug."""
        self._heuristics.append(h)

    @enforce_principle_v6(PrincipleV6.NT7_MICRO_PHENOMENA)
    @enforce_principle_v6(PrincipleV6.NT9_ROUND_TABLE_IS_CRITIC)
    def execute(self, context: FactoryBrainContext) -> FactoryBrainResult:
        brief = context.require_brief()
        report = CritiqueReport(brief_id=brief.brief_id)

        for h in self._heuristics:
            try:
                report.findings.extend(h.check(context))
            except Exception as exc:
                report.findings.append(CritiqueFinding(
                    heuristic_id=h.HEURISTIC_ID,
                    title=h.TITLE,
                    severity=CritiqueSeverity.ERROR,
                    message=f"Heuristic crashed: {type(exc).__name__}: {exc}",
                ))
            report.heuristics_run += 1

        context.shared_memory["critique_report"] = report.to_dict()

        warnings: List[str] = []
        if report.is_blocking:
            warnings.append(
                f"Brief có {report.error_count} ERROR - B4 KHÔNG nên chạy "
                f"cho đến khi C2 fix hoặc override."
            )

        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs={
                "critique": report.to_dict(),
                "is_blocking": report.is_blocking,
                "health_score": report.health_score(),
            },
            warnings=warnings,
            metrics={
                "heuristics_run": float(report.heuristics_run),
                "error_count": float(report.error_count),
                "warning_count": float(report.warning_count),
                "health_score": report.health_score(),
            },
            stage=self.BRAIN_STAGE.value,
        )


# ============================================================
# 7. SANITY CHECK
# ============================================================

def b3_design_critic_sanity_check() -> Dict[str, bool]:
    from apex_core.brains_v6.b1_intent_ingestor import BriefSpec

    checks: Dict[str, bool] = {}

    # Case 1: Brief "khỏe" - health_score cao
    healthy = BriefSpec(
        brief_id="b_healthy",
        raw_text="Landing page tối giản",
        domain="web",
        domain_confidence=0.9,
        product_type="landing_page",
        audience="founders",
        tone=("minimal", "editorial"),
        color_preferences=("navy",),
        features=("navbar", "hero", "cta", "pricing_table", "testimonials", "footer"),
        constraints={"max_bundle_kb": 300, "wcag_level": "AA"},
        references=("https://linear.app",),
        language="vi",
        parse_confidence=0.85,
    )
    ctx = FactoryBrainContext(
        run_id="r1", current_date="2025-01-01", draws=[], current_idx=0,
        brief_spec=healthy,
    )
    result = B3DesignCritic().run(ctx)
    checks["healthy_runs"] = result.success
    checks["healthy_not_blocking"] = not result.outputs["is_blocking"]
    checks["healthy_score_high"] = result.outputs["health_score"] >= 0.8

    # Case 2: Brief mâu thuẫn tone + bundle bất khả thi
    broken = BriefSpec(
        brief_id="b_broken",
        raw_text="Luxury playful minimal dashboard",
        domain="web",
        domain_confidence=0.9,
        product_type="dashboard",
        audience="",
        tone=("minimal", "playful", "luxury", "bold"),       # > 3 + conflicts
        color_preferences=("yellow", "white"),               # low contrast
        features=("hero", "testimonials"),                    # lạ cho dashboard
        constraints={"max_bundle_kb": 30, "wcag_level": "AA"},  # < baseline
        references=("not-a-url",),                            # format sai
        language="vi",
        parse_confidence=0.6,
    )
    ctx2 = FactoryBrainContext(
        run_id="r2", current_date="2025-01-01", draws=[], current_idx=0,
        brief_spec=broken,
        shared_memory={"slot_plan": {"missing_critical_features": ["navbar", "footer"]}},
    )
    result2 = B3DesignCritic().run(ctx2)
    checks["broken_runs"] = result2.success
    checks["broken_is_blocking"] = result2.outputs["is_blocking"]
    checks["broken_score_low"] = result2.outputs["health_score"] < 0.5

    # Check các heuristic cụ thể fire
    findings = result2.outputs["critique"]["findings"]
    fired_ids = {f["heuristic_id"] for f in findings}
    checks["h1_fired"] = "H1" in fired_ids
    checks["h2_fired"] = "H2" in fired_ids
    checks["h3_fired"] = "H3" in fired_ids
    checks["h4_fired"] = "H4" in fired_ids
    checks["h5_fired"] = "H5" in fired_ids
    checks["h6_fired"] = "H6" in fired_ids

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "B3_VERSION",
    "CritiqueSeverity",
    "CritiqueFinding",
    "TONE_HARD_CONFLICTS",
    "TONE_SOFT_AFFINITY",
    "UNUSUAL_FEATURES_FOR_PRODUCT",
    "FEATURE_ESTIMATED_KB",
    "BASELINE_BUNDLE_KB",
    "HeuristicBase",
    "H1_ToneCoherence",
    "H2_FeatureCoherence",
    "H3_BundleRealism",
    "H4_A11yFeasibility",
    "H5_ReferenceHealth",
    "H6_CriticalCompleteness",
    "H7_ScopeCreep",
    "CritiqueReport",
    "B3DesignCritic",
    "b3_design_critic_sanity_check",
]
