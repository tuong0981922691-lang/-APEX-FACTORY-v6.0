"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: b2_component_scout.py

Vai trò B2: COMPONENT SCOUT
    Input  : context.brief_spec (từ B1) + context.component_catalog
    Output : SlotPlan - với mỗi "slot nhu cầu" của brief (navbar, hero, ...)
             trả top-K ComponentSpec ứng viên đã chấm điểm.

Scoring 5 trục (thay cho 3 trục của B4 ConvergenceHunter cũ):
    1. CATEGORY_FIT      - đúng category (organism cho navbar, atom cho button)
    2. TAG_OVERLAP       - giao tag của component với tag kỳ vọng của feature
    3. TARGET_COMPAT     - HARD FILTER: spec.render_targets phải chứa target
    4. TONE_AFFINITY     - metadata.tone_hints giao với brief.tone
    5. CONFIDENCE_PRIOR  - parse_confidence của spec + provenance bonus

Quy tắc "thiếu thì báo" (NT6 - Không Kết Luận Ngẫu Nhiên):
    Nếu không có candidate nào pass hard filter, B2 KHÔNG bịa ra dàn giả
    mà gắn flag `needs_synthesis=True` cho slot đó để B4/B6 xử lý.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from apex_core.brains_v6.brain_base_v6 import (
    BrainStage,
    FactoryBrain,
    FactoryBrainContext,
    FactoryBrainResult,
)
from apex_core.foundation.ontology_ui import (
    ComponentCatalog,
    ComponentCategory,
    ComponentSpec,
    RenderTarget,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)

# ============================================================
# 0. VERSION
# ============================================================

B2_VERSION = "6.0.0"


# ============================================================
# 1. FEATURE → CATEGORY/TAG MAP
# ============================================================

@dataclass(frozen=True)
class FeatureRequirement:
    feature_id: str                     # tên chuẩn "navbar", "hero", ...
    preferred_categories: Tuple[ComponentCategory, ...]
    expected_tags: FrozenSet[str]
    is_critical: bool = False           # thiếu → fail page
    min_candidates_needed: int = 1
    max_candidates_to_return: int = 3


# Bảng tra chuẩn feature → yêu cầu. Có thể mở rộng runtime qua add_requirement().
DEFAULT_FEATURE_REQUIREMENTS: Tuple[FeatureRequirement, ...] = (
    FeatureRequirement(
        feature_id="navbar",
        preferred_categories=(ComponentCategory.ORGANISM,),
        expected_tags=frozenset({"nav", "navbar", "header_nav", "menu"}),
        is_critical=True,
    ),
    FeatureRequirement(
        feature_id="hero",
        preferred_categories=(ComponentCategory.ORGANISM, ComponentCategory.PATTERN),
        expected_tags=frozenset({"hero", "banner", "above_fold"}),
        is_critical=True,
    ),
    FeatureRequirement(
        feature_id="cta",
        preferred_categories=(ComponentCategory.ATOM, ComponentCategory.MOLECULE),
        expected_tags=frozenset({"cta", "button", "primary_action"}),
        is_critical=True,
    ),
    FeatureRequirement(
        feature_id="pricing_table",
        preferred_categories=(ComponentCategory.ORGANISM, ComponentCategory.PATTERN),
        expected_tags=frozenset({"pricing", "pricing_table", "plans"}),
    ),
    FeatureRequirement(
        feature_id="testimonials",
        preferred_categories=(ComponentCategory.ORGANISM,),
        expected_tags=frozenset({"testimonial", "social_proof", "review"}),
    ),
    FeatureRequirement(
        feature_id="faq",
        preferred_categories=(ComponentCategory.ORGANISM, ComponentCategory.MOLECULE),
        expected_tags=frozenset({"faq", "accordion", "qa"}),
    ),
    FeatureRequirement(
        feature_id="contact_form",
        preferred_categories=(ComponentCategory.ORGANISM, ComponentCategory.MOLECULE),
        expected_tags=frozenset({"form", "contact", "form_field"}),
    ),
    FeatureRequirement(
        feature_id="footer",
        preferred_categories=(ComponentCategory.ORGANISM,),
        expected_tags=frozenset({"footer"}),
        is_critical=True,
    ),
    FeatureRequirement(
        feature_id="auth",
        preferred_categories=(ComponentCategory.PATTERN, ComponentCategory.ORGANISM),
        expected_tags=frozenset({"auth", "login", "signup"}),
    ),
    FeatureRequirement(
        feature_id="search",
        preferred_categories=(ComponentCategory.MOLECULE,),
        expected_tags=frozenset({"search", "searchbar"}),
    ),
    FeatureRequirement(
        feature_id="dark_mode",
        preferred_categories=(ComponentCategory.ATOM, ComponentCategory.MOLECULE),
        expected_tags=frozenset({"theme_toggle", "dark_mode", "mode_switch"}),
    ),
    FeatureRequirement(
        feature_id="product_grid",
        preferred_categories=(ComponentCategory.ORGANISM,),
        expected_tags=frozenset({"product_grid", "catalog", "listing"}),
    ),
    FeatureRequirement(
        feature_id="cart",
        preferred_categories=(ComponentCategory.ORGANISM, ComponentCategory.PATTERN),
        expected_tags=frozenset({"cart", "shopping"}),
    ),
    FeatureRequirement(
        feature_id="checkout",
        preferred_categories=(ComponentCategory.PATTERN,),
        expected_tags=frozenset({"checkout", "payment"}),
    ),
    FeatureRequirement(
        feature_id="blog_list",
        preferred_categories=(ComponentCategory.ORGANISM,),
        expected_tags=frozenset({"blog", "article_list", "post_grid"}),
    ),
    FeatureRequirement(
        feature_id="animation",
        preferred_categories=(ComponentCategory.PATTERN,),
        expected_tags=frozenset({"animation", "motion", "scroll_effect"}),
    ),
)


# Product type → fallback feature set khi brief không khai báo đủ
PRODUCT_DEFAULT_FEATURES: Dict[str, Tuple[str, ...]] = {
    "landing_page": ("navbar", "hero", "cta", "footer"),
    "dashboard": ("navbar", "sidebar", "data_table"),
    "ecommerce": ("navbar", "product_grid", "cart", "footer"),
    "blog": ("navbar", "blog_list", "footer"),
    "portfolio": ("navbar", "hero", "footer"),
    "saas_app": ("navbar", "hero", "pricing_table", "cta", "footer"),
}


# ============================================================
# 2. CANDIDATE SCORING
# ============================================================

@dataclass(frozen=True)
class CandidateScore:
    """Điểm chi tiết của 1 component với 1 feature."""
    component_id: str
    category_fit: float                 # 0..1
    tag_overlap: float                  # 0..1
    target_compat: float                # 0 hoặc 1 (hard filter)
    tone_affinity: float                # 0..1
    confidence_prior: float             # 0..1
    composite: float                    # weighted sum
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScoringWeights:
    """Trọng số 5 trục. Tổng = 1.0 cho dễ đọc."""
    category_fit: float = 0.30
    tag_overlap: float = 0.30
    target_compat: float = 0.00         # hard filter, không cộng vào composite
    tone_affinity: float = 0.20
    confidence_prior: float = 0.20

    def __post_init__(self):
        soft_sum = self.category_fit + self.tag_overlap + self.tone_affinity + self.confidence_prior
        if abs(soft_sum - 1.0) > 1e-6:
            raise ValueError(
                f"Soft weights must sum to 1.0: got {soft_sum:.4f}"
            )


DEFAULT_SCORING_WEIGHTS = ScoringWeights()


class Scorer:
    def __init__(self, weights: ScoringWeights = DEFAULT_SCORING_WEIGHTS):
        self.weights = weights

    def score(
        self,
        spec: ComponentSpec,
        requirement: FeatureRequirement,
        target: RenderTarget,
        tone_preferences: FrozenSet[str],
    ) -> CandidateScore:
        # HARD FILTER: target compatibility
        if not spec.supports_target(target):
            return CandidateScore(
                component_id=spec.component_id,
                category_fit=0.0,
                tag_overlap=0.0,
                target_compat=0.0,
                tone_affinity=0.0,
                confidence_prior=0.0,
                composite=0.0,
                rejection_reason=f"target_{target.value}_not_supported",
            )

        # CATEGORY FIT
        cat_fit = 1.0 if spec.category in requirement.preferred_categories else 0.3

        # TAG OVERLAP (Jaccard đơn giản)
        spec_tags = frozenset(spec.tags)
        if requirement.expected_tags:
            intersection = spec_tags & requirement.expected_tags
            union = spec_tags | requirement.expected_tags
            tag_overlap = len(intersection) / max(len(union), 1)
        else:
            tag_overlap = 0.5

        # TONE AFFINITY (cần metadata.tone_hints trên spec - optional)
        tone_affinity = 0.5   # neutral baseline
        if tone_preferences:
            tone_hints = self._get_tone_hints(spec)
            if tone_hints:
                overlap = tone_preferences & tone_hints
                tone_affinity = min(1.0, 0.5 + 0.5 * (len(overlap) / max(len(tone_preferences), 1)))

        # CONFIDENCE PRIOR
        prior = spec.parse_confidence
        if spec.source_type == "manual":
            prior = min(1.0, prior * 1.05)   # nhẹ nhàng ưu ái manual
        elif spec.source_type == "evolved":
            prior *= 0.9                     # thận trọng với evolved

        # COMPOSITE
        w = self.weights
        composite = (
            w.category_fit * cat_fit
            + w.tag_overlap * tag_overlap
            + w.tone_affinity * tone_affinity
            + w.confidence_prior * prior
        )

        return CandidateScore(
            component_id=spec.component_id,
            category_fit=round(cat_fit, 4),
            tag_overlap=round(tag_overlap, 4),
            target_compat=1.0,
            tone_affinity=round(tone_affinity, 4),
            confidence_prior=round(prior, 4),
            composite=round(composite, 4),
        )

    @staticmethod
    def _get_tone_hints(spec: ComponentSpec) -> FrozenSet[str]:
        # ComponentSpec v6 chưa bake 'tone_hints' riêng; tạm lấy từ tags
        tone_keywords = {
            "minimal", "luxury", "playful", "corporate",
            "tech", "warm", "bold", "editorial",
        }
        return frozenset(t for t in spec.tags if t in tone_keywords)


# ============================================================
# 3. SLOT PLAN (output của B2)
# ============================================================

@dataclass
class SlotAssignment:
    """1 slot nhu cầu của brief + các candidate đã xếp hạng."""
    feature_id: str
    is_critical: bool
    top_candidates: List[CandidateScore] = field(default_factory=list)
    fallback_action: str = "ok"         # "ok" | "needs_synthesis" | "needs_llm_borrow"
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "is_critical": self.is_critical,
            "top_candidates": [c.to_dict() for c in self.top_candidates],
            "fallback_action": self.fallback_action,
            "note": self.note,
        }


@dataclass
class SlotPlan:
    """Full plan cho 1 brief."""
    brief_id: str
    target_render_target: str
    assignments: List[SlotAssignment] = field(default_factory=list)
    missing_critical_features: List[str] = field(default_factory=list)
    total_catalog_size: int = 0
    total_candidates_returned: int = 0

    @property
    def is_complete(self) -> bool:
        return len(self.missing_critical_features) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "target_render_target": self.target_render_target,
            "assignments": [a.to_dict() for a in self.assignments],
            "missing_critical_features": list(self.missing_critical_features),
            "total_catalog_size": self.total_catalog_size,
            "total_candidates_returned": self.total_candidates_returned,
            "is_complete": self.is_complete,
        }


# ============================================================
# 4. B2 COMPONENT SCOUT BRAIN
# ============================================================

class B2ComponentScout(FactoryBrain):
    BRAIN_ID = "B2_v6"
    BRAIN_NAME = "ComponentScout"
    BRAIN_STAGE = BrainStage.SCOUT
    REQUIRED_INPUTS = ()                # brief đọc từ context.brief_spec
    REQUIRED_CONTEXT_ATTRS = ("component_catalog", "brief_spec")

    def __init__(
        self,
        hooks=None,
        requirements: Optional[Sequence[FeatureRequirement]] = None,
        default_target: RenderTarget = RenderTarget.REACT,
        scorer: Optional[Scorer] = None,
    ):
        super().__init__(hooks=hooks)
        self._requirements: Dict[str, FeatureRequirement] = {
            r.feature_id: r for r in (requirements or DEFAULT_FEATURE_REQUIREMENTS)
        }
        self._default_target = default_target
        self._scorer = scorer or Scorer()

    def add_requirement(self, req: FeatureRequirement) -> None:
        """NT10 hot-plug - thêm feature mới runtime."""
        self._requirements[req.feature_id] = req

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    @enforce_principle_v6(PrincipleV6.NT6_NO_RANDOM_CONCLUSION)
    def execute(self, context: FactoryBrainContext) -> FactoryBrainResult:
        brief = context.require_brief()
        catalog = context.require_catalog()

        # Resolve target: ưu tiên brief.constraints['render_target'] nếu có
        target_str = brief.constraints.get("render_target")
        try:
            target = RenderTarget(target_str) if target_str else self._default_target
        except ValueError:
            target = self._default_target

        # Resolve feature set: brief.features + product default fallback
        feature_set = self._resolve_feature_set(brief)

        tone_prefs = frozenset(brief.tone)

        assignments: List[SlotAssignment] = []
        missing_critical: List[str] = []
        total_returned = 0

        for feature_id in feature_set:
            req = self._requirements.get(feature_id)
            if req is None:
                # Feature lạ - vẫn ghi nhận nhưng đánh dấu cần synthesis
                assignments.append(SlotAssignment(
                    feature_id=feature_id,
                    is_critical=False,
                    top_candidates=[],
                    fallback_action="needs_llm_borrow" if context.has_llm() else "needs_synthesis",
                    note=f"Feature '{feature_id}' chưa có FeatureRequirement đăng ký",
                ))
                continue

            candidates = self._scout_for_requirement(catalog, req, target, tone_prefs)

            # Filter out hard-rejected (target_compat=0)
            passed = [c for c in candidates if c.target_compat > 0]
            # Sort by composite desc
            passed.sort(key=lambda c: -c.composite)
            top_k = passed[:req.max_candidates_to_return]
            total_returned += len(top_k)

            if len(top_k) < req.min_candidates_needed:
                fallback = "needs_llm_borrow" if context.has_llm() else "needs_synthesis"
                note = (
                    f"Chỉ {len(top_k)}/{req.min_candidates_needed} candidate pass. "
                    f"Catalog hiện có {catalog.size()} components."
                )
                if req.is_critical:
                    missing_critical.append(feature_id)
            else:
                fallback = "ok"
                note = ""

            assignments.append(SlotAssignment(
                feature_id=feature_id,
                is_critical=req.is_critical,
                top_candidates=top_k,
                fallback_action=fallback,
                note=note,
            ))

        plan = SlotPlan(
            brief_id=brief.brief_id,
            target_render_target=target.value,
            assignments=assignments,
            missing_critical_features=missing_critical,
            total_catalog_size=catalog.size(),
            total_candidates_returned=total_returned,
        )

        context.shared_memory["slot_plan"] = plan.to_dict()

        warnings: List[str] = []
        if missing_critical:
            warnings.append(
                f"Thiếu {len(missing_critical)} feature critical: {missing_critical}. "
                f"B4/B6 cần synthesize hoặc mượn LLM."
            )
        if catalog.size() == 0:
            warnings.append(
                "Catalog trống - mọi slot đều cần synthesis. "
                "Hãy seed catalog qua ComponentCatalog.register() trước."
            )

        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs={
                "slot_plan": plan.to_dict(),
                "target": target.value,
                "features_requested": list(feature_set),
                "assignments_count": len(assignments),
                "missing_critical_count": len(missing_critical),
            },
            warnings=warnings,
            metrics={
                "catalog_size": float(catalog.size()),
                "features_requested": float(len(feature_set)),
                "total_candidates_returned": float(total_returned),
                "missing_critical": float(len(missing_critical)),
                "completeness": (
                    0.0 if len(feature_set) == 0
                    else 1.0 - (len(missing_critical) / max(len(feature_set), 1))
                ),
            },
            stage=self.BRAIN_STAGE.value,
        )

    def _resolve_feature_set(self, brief: Any) -> List[str]:
        """Lấy brief.features; nếu thiếu thì bù bằng PRODUCT_DEFAULT_FEATURES."""
        requested = list(brief.features)
        if requested:
            return requested
        # Fallback
        defaults = PRODUCT_DEFAULT_FEATURES.get(brief.product_type, ("hero", "cta", "footer"))
        return list(defaults)

    def _scout_for_requirement(
        self,
        catalog: ComponentCatalog,
        req: FeatureRequirement,
        target: RenderTarget,
        tone_prefs: FrozenSet[str],
    ) -> List[CandidateScore]:
        # Quét theo category trước để giảm chi phí
        pool: List[ComponentSpec] = []
        seen_ids: set = set()
        for category in req.preferred_categories:
            for spec in catalog.search_by_category(category):
                if spec.component_id not in seen_ids:
                    pool.append(spec)
                    seen_ids.add(spec.component_id)
        # Thêm: quét theo tag (mở rộng)
        for tag in req.expected_tags:
            for spec in catalog.search_by_tag(tag):
                if spec.component_id not in seen_ids:
                    pool.append(spec)
                    seen_ids.add(spec.component_id)

        return [
            self._scorer.score(spec, req, target, tone_prefs)
            for spec in pool
        ]


# ============================================================
# 5. SANITY CHECK
# ============================================================

def b2_component_scout_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ontology_ui import (
        A11yContract,
        A11yRole,
        ComponentState,
        PropSchema,
    )

    checks: Dict[str, bool] = {}

    # Seed catalog với 3 components: 1 navbar tốt, 1 navbar kém, 1 footer
    catalog = ComponentCatalog()
    catalog.register(ComponentSpec(
        component_id="organism.navbar.default",
        label="Default Navbar",
        category=ComponentCategory.ORGANISM,
        prop_schema=(PropSchema("brand", "string", required=True),),
        slots=(),
        states=(ComponentState.DEFAULT,),
        a11y=A11yContract(role=A11yRole.NAVIGATION),
        design_tokens_used=(),
        dependencies=(),
        render_targets=(RenderTarget.REACT,),
        tags=("nav", "navbar", "minimal"),
        parse_confidence=0.9,
    ))
    catalog.register(ComponentSpec(
        component_id="organism.navbar.complex",
        label="Complex Navbar",
        category=ComponentCategory.ORGANISM,
        prop_schema=(PropSchema("brand", "string", required=True),),
        slots=(),
        states=(ComponentState.DEFAULT,),
        a11y=A11yContract(role=A11yRole.NAVIGATION),
        design_tokens_used=(),
        dependencies=(),
        render_targets=(RenderTarget.VUE,),   # KHÔNG support React
        tags=("nav", "navbar"),
        parse_confidence=0.8,
    ))
    catalog.register(ComponentSpec(
        component_id="organism.footer.basic",
        label="Basic Footer",
        category=ComponentCategory.ORGANISM,
        prop_schema=(),
        slots=(),
        states=(ComponentState.DEFAULT,),
        a11y=A11yContract(role=A11yRole.FOOTER),
        design_tokens_used=(),
        dependencies=(),
        render_targets=(RenderTarget.REACT,),
        tags=("footer",),
        parse_confidence=0.85,
    ))

    # Build brief & context (giả)
    from apex_core.brains_v6.b1_intent_ingestor import BriefSpec

    brief = BriefSpec(
        brief_id="b_test",
        raw_text="Landing page tối giản",
        domain="web",
        domain_confidence=0.9,
        product_type="landing_page",
        audience="",
        tone=("minimal",),
        color_preferences=(),
        features=("navbar", "footer"),
        constraints={},
        references=(),
        language="vi",
        parse_confidence=0.7,
    )

    ctx = FactoryBrainContext(
        run_id="r_b2",
        current_date="2025-01-01",
        draws=[],
        current_idx=0,
        component_catalog=catalog,
        brief_spec=brief,
        target_domain=None,
    )

    brain = B2ComponentScout()
    result = brain.run(ctx)

    checks["run_success"] = result.success
    plan = result.outputs.get("slot_plan", {})
    assignments = plan.get("assignments", [])
    checks["two_assignments"] = len(assignments) == 2

    # Navbar assignment phải có 1 candidate pass (Vue bị reject bởi hard filter)
    navbar_asg = next((a for a in assignments if a["feature_id"] == "navbar"), None)
    if navbar_asg:
        checks["navbar_has_candidate"] = len(navbar_asg["top_candidates"]) >= 1
        if navbar_asg["top_candidates"]:
            top = navbar_asg["top_candidates"][0]
            checks["navbar_picks_react"] = top["component_id"] == "organism.navbar.default"
            checks["navbar_tone_boost"] = top["tone_affinity"] > 0.5

    # Footer assignment
    footer_asg = next((a for a in assignments if a["feature_id"] == "footer"), None)
    if footer_asg:
        checks["footer_ok"] = footer_asg["fallback_action"] == "ok"

    # Empty catalog case
    empty_ctx = FactoryBrainContext(
        run_id="r_empty",
        current_date="2025-01-01",
        draws=[],
        current_idx=0,
        component_catalog=ComponentCatalog(),
        brief_spec=brief,
    )
    result_empty = B2ComponentScout().run(empty_ctx)
    empty_plan = result_empty.outputs.get("slot_plan", {})
    checks["empty_catalog_missing_critical"] = (
        len(empty_plan.get("missing_critical_features", [])) >= 1
    )

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "B2_VERSION",
    "FeatureRequirement",
    "DEFAULT_FEATURE_REQUIREMENTS",
    "PRODUCT_DEFAULT_FEATURES",
    "CandidateScore",
    "ScoringWeights",
    "DEFAULT_SCORING_WEIGHTS",
    "Scorer",
    "SlotAssignment",
    "SlotPlan",
    "B2ComponentScout",
    "b2_component_scout_sanity_check",
]
