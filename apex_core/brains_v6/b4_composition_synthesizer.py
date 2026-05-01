"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: b4_composition_synthesizer.py

Vai trò B4: COMPOSITION SYNTHESIZER
    Sinh N=3 biến thể DesignGraph từ (brief, slot_plan, critique) để
    Radar 4D + Round Table (Phase 2) có nhiều lựa chọn đánh giá.

3 variant strategies (hội tụ 3 trục Purpose × Aesthetic × Technique):
    VARIANT_A - BASELINE   : an toàn, kế thừa cao, density comfortable
    VARIANT_B - BOLD       : contrast cao, motion mạnh, creative
    VARIANT_C - LEAN       : tối giản tuyệt đối, ít motion, bundle nhẹ

Graceful degradation:
    Nếu slot thiếu candidate → tạo PlaceholderNode với
    metadata.needs_llm_fill=True để B6 mượn LLM bổ sung.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from apex_core.brains_v6.brain_base_v6 import (
    BrainStage,
    FactoryBrain,
    FactoryBrainContext,
    FactoryBrainResult,
)
from apex_core.foundation.ontology_ui import (
    ComponentCatalog,
    ComponentCategory,
    RenderTarget,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.ui_ir import (
    DesignGraph,
    DesignGraphBuilder,
    DesignNode,
)

# ============================================================
# 0. VERSION
# ============================================================

B4_VERSION = "6.0.0"


# ============================================================
# 1. VARIANT STRATEGY
# ============================================================

class VariantStrategy(str, Enum):
    BASELINE = "A_baseline"
    BOLD = "B_bold"
    LEAN = "C_lean"


@dataclass(frozen=True)
class VariantProfile:
    strategy: VariantStrategy
    density: str                        # "compact" | "comfortable" | "spacious"
    motion_intensity: float             # 0..1
    contrast_preference: str            # "standard" | "high" | "subtle"
    candidate_pick_index: int           # 0 = top pick; 1/2 = alternates
    include_animation_layer: bool
    theme_default: str                  # "light" | "dark"
    note: str


VARIANT_PROFILES: Dict[VariantStrategy, VariantProfile] = {
    VariantStrategy.BASELINE: VariantProfile(
        strategy=VariantStrategy.BASELINE,
        density="comfortable",
        motion_intensity=0.3,
        contrast_preference="standard",
        candidate_pick_index=0,
        include_animation_layer=True,
        theme_default="light",
        note="Safe pick - dùng top candidate + tone trung tính",
    ),
    VariantStrategy.BOLD: VariantProfile(
        strategy=VariantStrategy.BOLD,
        density="spacious",
        motion_intensity=0.7,
        contrast_preference="high",
        candidate_pick_index=1,
        include_animation_layer=True,
        theme_default="dark",
        note="Creative - contrast cao, motion mạnh, theme dark default",
    ),
    VariantStrategy.LEAN: VariantProfile(
        strategy=VariantStrategy.LEAN,
        density="compact",
        motion_intensity=0.0,
        contrast_preference="subtle",
        candidate_pick_index=0,
        include_animation_layer=False,
        theme_default="light",
        note="Minimalist - bundle nhẹ, no motion, cực an toàn",
    ),
}


# ============================================================
# 2. PLACEHOLDER COMPONENT ID (khi catalog trống)
# ============================================================

PLACEHOLDER_COMPONENT_IDS: Dict[str, str] = {
    "page":    "placeholder.page.container",
    "navbar":  "placeholder.organism.navbar",
    "hero":    "placeholder.organism.hero",
    "cta":     "placeholder.atom.cta_button",
    "footer":  "placeholder.organism.footer",
    "section": "placeholder.organism.section",
}


# ============================================================
# 3. SYNTHESIZER SERVICE
# ============================================================

class CompositionSynthesizer:
    """Service nguyên tắc NT4 - chỉ lắp ghép, không tạo ngoài khuôn."""

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    @enforce_principle_v6(PrincipleV6.NT1_MULTI_AXIS_CONVERGENCE)
    def synthesize(
        self,
        brief_dict: Dict[str, Any],
        slot_plan: Dict[str, Any],
        profile: VariantProfile,
        catalog: ComponentCatalog,
        target: RenderTarget,
    ) -> Tuple[DesignGraph, List[str]]:
        """Build 1 DesignGraph cho 1 variant. Trả (graph, warnings)."""
        warnings: List[str] = []

        # Root: tìm component 'page.*' từ catalog hoặc placeholder
        root_component = self._pick_root_component(brief_dict, catalog)
        if root_component is None:
            root_component = PLACEHOLDER_COMPONENT_IDS["page"]
            warnings.append("Page root component không có trong catalog - dùng placeholder")

        builder = DesignGraphBuilder(target=target, graph_id=self._gen_id("g"))
        builder.root(
            root_component,
            node_id="n_root",
            props={
                "theme": profile.theme_default,
                "density": profile.density,
            },
        )

        # Attach meta pairs để SemanticPairingRule không fire
        builder._graph.metadata["semantic_pairs"] = {
            "theme.light_dark": ["light", "dark"],
        }
        builder._graph.metadata["variant_strategy"] = profile.strategy.value
        builder._graph.metadata["motion_intensity"] = profile.motion_intensity
        builder._graph.metadata["contrast_preference"] = profile.contrast_preference

        # Duyệt assignments của SlotPlan theo thứ tự
        assignments = slot_plan.get("assignments", [])
        for asg in assignments:
            feature_id = asg["feature_id"]
            candidates = asg.get("top_candidates", [])
            fallback_action = asg.get("fallback_action", "ok")
            is_critical = asg.get("is_critical", False)

            component_id: Optional[str] = None
            needs_llm_fill = False

            if candidates:
                # Pick theo profile.candidate_pick_index với safe clamp
                idx = min(profile.candidate_pick_index, len(candidates) - 1)
                component_id = candidates[idx]["component_id"]
            else:
                # Không có → placeholder + cờ LLM fill
                component_id = PLACEHOLDER_COMPONENT_IDS.get(
                    feature_id, PLACEHOLDER_COMPONENT_IDS["section"]
                )
                needs_llm_fill = (fallback_action == "needs_llm_borrow")
                warnings.append(
                    f"Feature '{feature_id}' dùng placeholder "
                    f"(needs_llm_fill={needs_llm_fill}, critical={is_critical})"
                )

            node_id = f"n_{feature_id}_{self._gen_short()}"
            node = DesignNode(
                node_id=node_id,
                component_id=component_id,
                metadata={
                    "feature_id": feature_id,
                    "needs_llm_fill": needs_llm_fill,
                    "is_critical": is_critical,
                    "variant_strategy": profile.strategy.value,
                },
            )
            # Inject animation flag
            if profile.include_animation_layer and feature_id in ("hero", "cta", "pricing_table"):
                node.metadata["has_animation"] = True
                node.metadata["motion_intensity"] = profile.motion_intensity

            builder._graph.add_node(node)
            builder._graph.link("n_root", "main", node_id)

        # Build WITHOUT strict catalog validation (vì có placeholder)
        graph = builder._graph
        return graph, warnings

    def _pick_root_component(
        self,
        brief_dict: Dict[str, Any],
        catalog: ComponentCatalog,
    ) -> Optional[str]:
        page_candidates = catalog.search_by_category(ComponentCategory.PAGE)
        if not page_candidates:
            return None
        # Ưu tiên component có tag khớp product_type
        product_type = brief_dict.get("product_type", "")
        for c in page_candidates:
            if product_type in c.tags:
                return c.component_id
        return page_candidates[0].component_id

    @staticmethod
    def _gen_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _gen_short() -> str:
        return uuid.uuid4().hex[:6]


# ============================================================
# 4. B4 COMPOSITION SYNTHESIZER BRAIN
# ============================================================

class B4CompositionSynthesizer(FactoryBrain):
    BRAIN_ID = "B4_v6"
    BRAIN_NAME = "CompositionSynthesizer"
    BRAIN_STAGE = BrainStage.SYNTHESIZE
    REQUIRED_CONTEXT_ATTRS = ("component_catalog", "brief_spec")

    def __init__(
        self,
        hooks=None,
        variant_strategies: Optional[List[VariantStrategy]] = None,
        default_target: RenderTarget = RenderTarget.REACT,
    ):
        super().__init__(hooks=hooks)
        self._strategies = variant_strategies or [
            VariantStrategy.BASELINE,
            VariantStrategy.BOLD,
            VariantStrategy.LEAN,
        ]
        self._default_target = default_target
        self._synth = CompositionSynthesizer()

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def execute(self, context: FactoryBrainContext) -> FactoryBrainResult:
        # Check critique report - blocking thì abort
        critique = context.shared_memory.get("critique_report", {})
        if critique.get("is_blocking"):
            allow_override = context.shared_memory.get("c2_override_blocking", False)
            if not allow_override:
                return FactoryBrainResult(
                    brain_id=self.BRAIN_ID,
                    success=False,
                    outputs={"reason": "critique_blocking"},
                    errors=[
                        f"B3 báo {critique.get('error_count', 0)} ERROR - B4 abort. "
                        f"C2 phải fix brief hoặc set c2_override_blocking=True."
                    ],
                    stage=self.BRAIN_STAGE.value,
                )

        brief = context.require_brief()
        brief_dict = brief.to_dict()
        slot_plan = context.shared_memory.get("slot_plan", {})
        catalog = context.require_catalog()

        # Resolve target
        target_str = brief.constraints.get("render_target")
        try:
            target = RenderTarget(target_str) if target_str else self._default_target
        except ValueError:
            target = self._default_target

        variants: List[DesignGraph] = []
        all_warnings: List[str] = []
        variant_summaries: List[Dict[str, Any]] = []

        for strategy in self._strategies:
            profile = VARIANT_PROFILES[strategy]
            try:
                graph, warnings = self._synth.synthesize(
                    brief_dict=brief_dict,
                    slot_plan=slot_plan,
                    profile=profile,
                    catalog=catalog,
                    target=target,
                )
                variants.append(graph)
                all_warnings.extend(f"[{strategy.value}] {w}" for w in warnings)
                variant_summaries.append({
                    "strategy": strategy.value,
                    "graph_id": graph.graph_id,
                    "node_count": len(graph.nodes),
                    "placeholder_count": sum(
                        1 for n in graph.nodes.values()
                        if n.component_id.startswith("placeholder.")
                    ),
                    "warnings": warnings,
                })
            except Exception as e:
                all_warnings.append(f"[{strategy.value}] synth failed: {type(e).__name__}: {e}")
                variant_summaries.append({
                    "strategy": strategy.value,
                    "graph_id": None,
                    "error": str(e),
                })

        if not variants:
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID,
                success=False,
                outputs={},
                errors=["Không sinh được variant nào"],
                warnings=all_warnings,
                stage=self.BRAIN_STAGE.value,
            )

        # Attach vào context
        context.variant_graphs = variants
        context.active_design_graph = variants[0]   # baseline = default

        # Lưu dict version vào shared_memory cho B6 đọc
        context.shared_memory["variant_graphs_dicts"] = [g.to_dict() for g in variants]
        context.shared_memory["active_graph_id"] = variants[0].graph_id

        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs={
                "variants": variant_summaries,
                "variants_count": len(variants),
                "active_graph_id": variants[0].graph_id,
                "target": target.value,
            },
            warnings=all_warnings,
            metrics={
                "variants_produced": float(len(variants)),
                "avg_nodes_per_variant": float(
                    sum(len(g.nodes) for g in variants) / len(variants)
                ),
                "total_placeholders": float(sum(
                    1
                    for g in variants
                    for n in g.nodes.values()
                    if n.component_id.startswith("placeholder.")
                )),
            },
            stage=self.BRAIN_STAGE.value,
            graph_diff_summary={"strategies_run": [s.value for s in self._strategies]},
        )


# ============================================================
# 5. SANITY CHECK
# ============================================================

def b4_composition_synthesizer_sanity_check() -> Dict[str, bool]:
    from apex_core.brains_v6.b1_intent_ingestor import BriefSpec

    checks: Dict[str, bool] = {}
    brief = BriefSpec(
        brief_id="b1", raw_text="Landing", domain="web", domain_confidence=0.9,
        product_type="landing_page", audience="", tone=("minimal",),
        color_preferences=(), features=("navbar", "hero", "cta", "footer"),
        constraints={}, references=(), language="vi", parse_confidence=0.8,
    )
    slot_plan = {
        "assignments": [
            {"feature_id": "navbar", "is_critical": True, "top_candidates": [], "fallback_action": "needs_synthesis"},
            {"feature_id": "hero",   "is_critical": True, "top_candidates": [], "fallback_action": "needs_synthesis"},
            {"feature_id": "cta",    "is_critical": True, "top_candidates": [], "fallback_action": "needs_synthesis"},
            {"feature_id": "footer", "is_critical": True, "top_candidates": [], "fallback_action": "needs_synthesis"},
        ],
    }
    ctx = FactoryBrainContext(
        run_id="r", current_date="2025-01-01", draws=[], current_idx=0,
        brief_spec=brief, component_catalog=ComponentCatalog(),
        shared_memory={"slot_plan": slot_plan, "critique_report": {"is_blocking": False}},
    )
    result = B4CompositionSynthesizer().run(ctx)
    checks["run_success"] = result.success
    checks["three_variants"] = result.outputs.get("variants_count") == 3
    checks["active_graph_set"] = ctx.active_design_graph is not None
    checks["placeholders_used"] = result.metrics.get("total_placeholders", 0) > 0

    # Blocking abort
    ctx2 = FactoryBrainContext(
        run_id="r2", current_date="2025-01-01", draws=[], current_idx=0,
        brief_spec=brief, component_catalog=ComponentCatalog(),
        shared_memory={"slot_plan": slot_plan, "critique_report": {"is_blocking": True, "error_count": 2}},
    )
    result2 = B4CompositionSynthesizer().run(ctx2)
    checks["blocking_aborts"] = not result2.success
    return checks


__all__ = [
    "B4_VERSION", "VariantStrategy", "VariantProfile", "VARIANT_PROFILES",
    "PLACEHOLDER_COMPONENT_IDS", "CompositionSynthesizer",
    "B4CompositionSynthesizer", "b4_composition_synthesizer_sanity_check",
]
