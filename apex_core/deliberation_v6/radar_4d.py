"""
APEX FACTORY v6.0 - Deliberation Layer (v6)
File: radar_4d.py

Mục đích: RADAR 4D SCORER - chấm điểm 1 DesignGraph theo 4 trục.
    X - SPEED       : tốc độ render ước tính (LCP/TBT/INP proxy)
    Y - FOOTPRINT   : bundle size, RAM footprint
    Z - STABILITY   : độ phức tạp cấu trúc, coupling, type-risk
    T - CLEANLINESS : MDL Prior (Minimum Description Length) + duplication

LƯU Ý Ở PHASE 2: đây là FORECAST từ graph topology, KHÔNG phải đo thực.
                 Phase 3 Preview Sandbox sẽ chạy Lighthouse/build thật.
                 Radar 4D v6 đóng vai trò "quick screen" trước sandbox.

MDL Prior (NT4 - Constrained Creativity):
    Code/graph quá dài cho cùng chức năng sẽ bị trừ điểm. Công thức:
        mdl_penalty = max(0, (actual_nodes / expected_nodes - 1.20))
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Tuple

from apex_core.foundation.ontology_ui import (
    ComponentCatalog,
    ComponentCategory,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.ui_ir import DesignGraph, DesignNode

# ============================================================
# 0. VERSION + CONSTANTS
# ============================================================

RADAR_4D_VERSION = "6.0.0"


class RadarAxis(str, Enum):
    SPEED = "X_speed"
    FOOTPRINT = "Y_footprint"
    STABILITY = "Z_stability"
    CLEANLINESS = "T_cleanliness"


# ============================================================
# 1. AXIS SCORE DATACLASS
# ============================================================

@dataclass(frozen=True)
class AxisScore:
    axis: RadarAxis
    raw_value: float                    # giá trị thô (ms, kb, cyclomatic, ...)
    normalized_score: float             # 0..1 (1 = tốt nhất)
    grade: str                          # "A" | "B" | "C" | "D" | "F"
    breakdown: Mapping[str, float]      # thành phần chi tiết
    warnings: Tuple[str, ...] = ()

    def __post_init__(self):
        if not (0.0 <= self.normalized_score <= 1.0):
            raise ValueError(
                f"normalized_score out of [0,1]: {self.normalized_score}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "axis": self.axis.value,
            "raw_value": self.raw_value,
            "normalized_score": round(self.normalized_score, 4),
            "grade": self.grade,
            "breakdown": {k: round(v, 4) for k, v in self.breakdown.items()},
            "warnings": list(self.warnings),
        }


def score_to_grade(score: float) -> str:
    if score >= 0.90: return "A"
    if score >= 0.75: return "B"
    if score >= 0.60: return "C"
    if score >= 0.40: return "D"
    return "F"


# ============================================================
# 2. AXIS SCORER BASE + IMPLEMENTATIONS
# ============================================================

class AxisScorer:
    AXIS: RadarAxis = RadarAxis.SPEED

    def score(
        self,
        graph: DesignGraph,
        catalog: ComponentCatalog,
        brief_constraints: Mapping[str, Any],
    ) -> AxisScore:
        raise NotImplementedError


# ---------------- X: SPEED ----------------

# Heuristic weights (ms budget)
NODE_RENDER_COST_MS = 0.8       # Mỗi node = 0.8ms render
ANIMATION_COST_MS = 15.0        # Mỗi node có animation = +15ms
DATA_BINDING_COST_MS = 50.0     # Mỗi data binding (REST) = 50ms + network
PLACEHOLDER_COST_MS = 10.0      # Placeholder = uncertain render


class SpeedScorer(AxisScorer):
    AXIS = RadarAxis.SPEED

    # Target ngưỡng "good" theo Core Web Vitals
    TARGET_LCP_MS = 2500.0

    def score(self, graph, catalog, brief_constraints):
        node_count = len(graph.nodes)
        animation_count = sum(
            1 for n in graph.nodes.values() if n.metadata.get("has_animation")
        )
        binding_count = sum(
            len(n.data_bindings) for n in graph.nodes.values()
        )
        placeholder_count = sum(
            1 for n in graph.nodes.values()
            if n.component_id.startswith("placeholder.")
        )

        estimated_lcp_ms = (
            node_count * NODE_RENDER_COST_MS
            + animation_count * ANIMATION_COST_MS
            + binding_count * DATA_BINDING_COST_MS
            + placeholder_count * PLACEHOLDER_COST_MS
        )

        # Adjust theo user-declared constraint
        target = brief_constraints.get("max_lcp_seconds")
        target_ms = float(target) * 1000 if target else self.TARGET_LCP_MS

        # Normalize: score = clamp(1 - (est/target - 1), 0, 1)
        # est <= target → score 1; est = 2*target → score 0
        ratio = estimated_lcp_ms / max(target_ms, 100)
        score = max(0.0, min(1.0, 2.0 - ratio))

        warnings: List[str] = []
        if estimated_lcp_ms > target_ms:
            warnings.append(
                f"Estimated LCP {estimated_lcp_ms:.0f}ms > target {target_ms:.0f}ms"
            )
        if placeholder_count > 0:
            warnings.append(
                f"{placeholder_count} placeholder nodes - speed estimate unreliable"
            )
        if animation_count > 5:
            warnings.append(f"{animation_count} animation nodes - may cause TBT spikes")

        return AxisScore(
            axis=self.AXIS,
            raw_value=round(estimated_lcp_ms, 1),
            normalized_score=round(score, 4),
            grade=score_to_grade(score),
            breakdown={
                "node_render_ms": round(node_count * NODE_RENDER_COST_MS, 2),
                "animation_ms": round(animation_count * ANIMATION_COST_MS, 2),
                "binding_ms": round(binding_count * DATA_BINDING_COST_MS, 2),
                "placeholder_ms": round(placeholder_count * PLACEHOLDER_COST_MS, 2),
                "estimated_lcp_ms": round(estimated_lcp_ms, 1),
                "target_lcp_ms": target_ms,
            },
            warnings=tuple(warnings),
        )


# ---------------- Y: FOOTPRINT ----------------

# KB estimate mỗi component category (gzipped JS)
CATEGORY_KB_ESTIMATE: Dict[ComponentCategory, float] = {
    ComponentCategory.ATOM: 2.5,
    ComponentCategory.MOLECULE: 6.0,
    ComponentCategory.ORGANISM: 12.0,
    ComponentCategory.TEMPLATE: 8.0,
    ComponentCategory.PAGE: 5.0,
    ComponentCategory.PATTERN: 15.0,
    ComponentCategory.LAYOUT: 3.0,
}
FRAMEWORK_BASELINE_KB = 45.0          # React + TS runtime shell
PLACEHOLDER_KB_PENALTY = 8.0          # placeholder = unknown, assume medium


class FootprintScorer(AxisScorer):
    AXIS = RadarAxis.FOOTPRINT
    TARGET_BUNDLE_KB_DEFAULT = 250.0

    def score(self, graph, catalog, brief_constraints):
        unique_components = set()
        category_counts: Dict[str, int] = {}
        placeholder_count = 0

        for n in graph.nodes.values():
            if n.component_id.startswith("placeholder."):
                placeholder_count += 1
                continue
            unique_components.add(n.component_id)

        total_kb = FRAMEWORK_BASELINE_KB
        for cid in unique_components:
            spec = catalog.get(cid)
            if spec is None:
                total_kb += 10.0      # unknown - conservative estimate
                continue
            kb = CATEGORY_KB_ESTIMATE.get(spec.category, 8.0)
            total_kb += kb
            category_counts[spec.category.value] = category_counts.get(spec.category.value, 0) + 1

        total_kb += placeholder_count * PLACEHOLDER_KB_PENALTY

        target = brief_constraints.get("max_bundle_kb") or self.TARGET_BUNDLE_KB_DEFAULT
        target = float(target)

        ratio = total_kb / max(target, 50.0)
        score = max(0.0, min(1.0, 2.0 - ratio))

        warnings: List[str] = []
        if total_kb > target:
            warnings.append(
                f"Estimated bundle {total_kb:.0f}kb > target {target:.0f}kb"
            )
        if placeholder_count > 3:
            warnings.append(
                f"{placeholder_count} placeholders → bundle estimate imprecise ±20%"
            )

        return AxisScore(
            axis=self.AXIS,
            raw_value=round(total_kb, 1),
            normalized_score=round(score, 4),
            grade=score_to_grade(score),
            breakdown={
                "framework_baseline_kb": FRAMEWORK_BASELINE_KB,
                "unique_components_count": len(unique_components),
                "placeholder_count": placeholder_count,
                "total_bundle_kb": round(total_kb, 1),
                "target_bundle_kb": target,
            },
            warnings=tuple(warnings),
        )


# ---------------- Z: STABILITY ----------------

class StabilityScorer(AxisScorer):
    AXIS = RadarAxis.STABILITY

    def score(self, graph, catalog, brief_constraints):
        # Depth: DFS longest path từ root
        max_depth = 0
        for depth, _ in graph.walk():
            if depth > max_depth:
                max_depth = depth

        # Branching factor trung bình
        branching: List[int] = []
        for n in graph.nodes.values():
            total_children = sum(len(ids) for ids in n.children_by_slot.values())
            if total_children > 0:
                branching.append(total_children)
        avg_branching = sum(branching) / len(branching) if branching else 0.0
        max_branching = max(branching) if branching else 0

        # Coupling: số data_bindings tổng
        coupling = sum(len(n.data_bindings) for n in graph.nodes.values())

        # Type-risk: placeholder = type unknown = risk cao
        placeholder_count = sum(
            1 for n in graph.nodes.values()
            if n.component_id.startswith("placeholder.")
        )
        type_risk = placeholder_count / max(len(graph.nodes), 1)

        # Missing required prop risk (validate against catalog)
        missing_props = 0
        for n in graph.nodes.values():
            spec = catalog.get(n.component_id)
            if spec is None:
                continue
            for prop in spec.prop_schema:
                if prop.required and prop.name not in n.props and prop.name not in n.data_bindings:
                    missing_props += 1

        # Normalize từng thành phần
        depth_score = 1.0 if max_depth <= 5 else max(0.0, 1.0 - (max_depth - 5) * 0.12)
        branching_score = 1.0 if max_branching <= 8 else max(0.0, 1.0 - (max_branching - 8) * 0.08)
        coupling_score = 1.0 if coupling <= 10 else max(0.0, 1.0 - (coupling - 10) * 0.05)
        type_score = 1.0 - min(1.0, type_risk)
        props_score = 1.0 if missing_props == 0 else max(0.0, 1.0 - missing_props * 0.15)

        composite = (
            0.20 * depth_score
            + 0.15 * branching_score
            + 0.20 * coupling_score
            + 0.20 * type_score
            + 0.25 * props_score
        )

        warnings: List[str] = []
        if max_depth > 8:
            warnings.append(f"Depth {max_depth} > 8 - nested hell risk")
        if max_branching > 10:
            warnings.append(f"Max branching {max_branching} > 10 - consider grouping")
        if missing_props > 0:
            warnings.append(f"{missing_props} required prop(s) missing - build will break")
        if type_risk > 0.3:
            warnings.append(f"Type-risk {type_risk:.0%} - too many placeholders")

        return AxisScore(
            axis=self.AXIS,
            raw_value=round(composite, 4),
            normalized_score=round(composite, 4),
            grade=score_to_grade(composite),
            breakdown={
                "max_depth": float(max_depth),
                "avg_branching": round(avg_branching, 3),
                "max_branching": float(max_branching),
                "coupling_bindings": float(coupling),
                "type_risk": round(type_risk, 4),
                "missing_required_props": float(missing_props),
                "depth_score": round(depth_score, 4),
                "branching_score": round(branching_score, 4),
                "coupling_score": round(coupling_score, 4),
                "type_score": round(type_score, 4),
                "props_score": round(props_score, 4),
            },
            warnings=tuple(warnings),
        )


# ---------------- T: CLEANLINESS (MDL Prior) ----------------

# Expected nodes cho 1 product_type chuẩn (từ heuristic PRODUCT_DEFAULT)
EXPECTED_NODES_BY_PRODUCT: Dict[str, int] = {
    "landing_page": 6,
    "dashboard": 12,
    "ecommerce": 10,
    "blog": 6,
    "portfolio": 6,
    "saas_app": 10,
}


class CleanlinessScorer(AxisScorer):
    AXIS = RadarAxis.CLEANLINESS

    def score(self, graph, catalog, brief_constraints):
        node_count = len(graph.nodes)
        product_type = brief_constraints.get("_product_type", "landing_page")
        expected = EXPECTED_NODES_BY_PRODUCT.get(product_type, 8)

        # MDL Prior: nếu actual > 1.20 * expected → penalty
        mdl_ratio = node_count / max(expected, 1)
        mdl_penalty = max(0.0, mdl_ratio - 1.20)
        mdl_score = max(0.0, 1.0 - mdl_penalty * 0.5)

        # Duplication: % component_id trùng
        component_counts: Dict[str, int] = {}
        for n in graph.nodes.values():
            component_counts[n.component_id] = component_counts.get(n.component_id, 0) + 1
        duplicates = sum(c - 1 for c in component_counts.values() if c > 1)
        dup_ratio = duplicates / max(node_count, 1)
        dup_score = max(0.0, 1.0 - dup_ratio * 0.8)    # lặp vừa phải OK

        # Props bloat: prop count per node trung bình
        avg_props = (
            sum(len(n.props) for n in graph.nodes.values()) / max(node_count, 1)
        )
        props_score = 1.0 if avg_props <= 6 else max(0.0, 1.0 - (avg_props - 6) * 0.08)

        # Placeholder ratio (cleaner = ít placeholder)
        placeholder_count = sum(
            1 for n in graph.nodes.values()
            if n.component_id.startswith("placeholder.")
        )
        placeholder_ratio = placeholder_count / max(node_count, 1)
        placeholder_score = 1.0 - min(1.0, placeholder_ratio)

        composite = (
            0.35 * mdl_score
            + 0.20 * dup_score
            + 0.20 * props_score
            + 0.25 * placeholder_score
        )

        warnings: List[str] = []
        if mdl_penalty > 0:
            warnings.append(
                f"MDL: {node_count} nodes > 1.20 × expected ({expected}) - verbose graph"
            )
        if dup_ratio > 0.3:
            warnings.append(f"Duplication {dup_ratio:.0%} high")
        if placeholder_ratio > 0.4:
            warnings.append(f"Placeholder ratio {placeholder_ratio:.0%} - not production-ready")

        return AxisScore(
            axis=self.AXIS,
            raw_value=round(composite, 4),
            normalized_score=round(composite, 4),
            grade=score_to_grade(composite),
            breakdown={
                "node_count": float(node_count),
                "expected_nodes": float(expected),
                "mdl_ratio": round(mdl_ratio, 4),
                "mdl_penalty": round(mdl_penalty, 4),
                "duplication_ratio": round(dup_ratio, 4),
                "avg_props_per_node": round(avg_props, 2),
                "placeholder_ratio": round(placeholder_ratio, 4),
                "mdl_score": round(mdl_score, 4),
                "dup_score": round(dup_score, 4),
                "props_score": round(props_score, 4),
                "placeholder_score": round(placeholder_score, 4),
            },
            warnings=tuple(warnings),
        )


# ============================================================
# 3. COMPOSITE REPORT
# ============================================================

@dataclass(frozen=True)
class RadarWeights:
    speed: float = 0.30
    footprint: float = 0.25
    stability: float = 0.25
    cleanliness: float = 0.20

    def __post_init__(self):
        total = self.speed + self.footprint + self.stability + self.cleanliness
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Radar weights must sum to 1.0, got {total}")


@dataclass
class Radar4DReport:
    graph_id: str
    axes: List[AxisScore]
    composite: float
    composite_grade: str
    total_warnings: int
    weights_used: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "composite": round(self.composite, 4),
            "composite_grade": self.composite_grade,
            "total_warnings": self.total_warnings,
            "weights_used": self.weights_used,
            "axes": [a.to_dict() for a in self.axes],
        }

    def get_axis(self, axis: RadarAxis) -> Optional[AxisScore]:
        for a in self.axes:
            if a.axis == axis:
                return a
        return None


# ============================================================
# 4. RADAR 4D SCORER (composite)
# ============================================================

class Radar4DScorer:
    def __init__(
        self,
        weights: Optional[RadarWeights] = None,
        scorers: Optional[List[AxisScorer]] = None,
    ):
        self.weights = weights or RadarWeights()
        self.scorers = scorers or [
            SpeedScorer(), FootprintScorer(),
            StabilityScorer(), CleanlinessScorer(),
        ]

    @enforce_principle_v6(PrincipleV6.NT6_NO_RANDOM_CONCLUSION)
    def evaluate(
        self,
        graph: DesignGraph,
        catalog: ComponentCatalog,
        brief_constraints: Optional[Mapping[str, Any]] = None,
    ) -> Radar4DReport:
        constraints = dict(brief_constraints or {})
        axis_scores: List[AxisScore] = []
        for scorer in self.scorers:
            axis_scores.append(scorer.score(graph, catalog, constraints))

        # Weighted composite
        w = self.weights
        composite = 0.0
        for a in axis_scores:
            if a.axis == RadarAxis.SPEED:
                composite += w.speed * a.normalized_score
            elif a.axis == RadarAxis.FOOTPRINT:
                composite += w.footprint * a.normalized_score
            elif a.axis == RadarAxis.STABILITY:
                composite += w.stability * a.normalized_score
            elif a.axis == RadarAxis.CLEANLINESS:
                composite += w.cleanliness * a.normalized_score

        total_warnings = sum(len(a.warnings) for a in axis_scores)

        return Radar4DReport(
            graph_id=graph.graph_id,
            axes=axis_scores,
            composite=round(composite, 4),
            composite_grade=score_to_grade(composite),
            total_warnings=total_warnings,
            weights_used={
                "speed": w.speed,
                "footprint": w.footprint,
                "stability": w.stability,
                "cleanliness": w.cleanliness,
            },
        )

    def rank_variants(
        self,
        graphs: List[DesignGraph],
        catalog: ComponentCatalog,
        brief_constraints: Optional[Mapping[str, Any]] = None,
    ) -> List[Radar4DReport]:
        """Chấm nhiều variant, trả theo thứ tự composite giảm dần."""
        reports = [self.evaluate(g, catalog, brief_constraints) for g in graphs]
        reports.sort(key=lambda r: -r.composite)
        return reports


# ============================================================
# 5. SANITY CHECK
# ============================================================

def radar_4d_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ui_ir import RenderTarget
    checks: Dict[str, bool] = {}

    # Build graph với 5 node đơn giản
    g = DesignGraph(graph_id="g_radar", target=RenderTarget.REACT, root_id="root")
    g.add_node(DesignNode(node_id="root", component_id="page.landing"))
    for i, cid in enumerate(["organism.navbar", "organism.hero", "atom.cta", "organism.footer"]):
        nid = f"n{i}"
        g.add_node(DesignNode(node_id=nid, component_id=cid))
        g.link("root", "main", nid)

    # Catalog trống OK (các scorer dùng default KB)
    catalog = ComponentCatalog()
    scorer = Radar4DScorer()
    report = scorer.evaluate(g, catalog, {"_product_type": "landing_page"})

    checks["four_axes_returned"] = len(report.axes) == 4
    checks["composite_in_range"] = 0.0 <= report.composite <= 1.0
    checks["has_grade"] = report.composite_grade in {"A", "B", "C", "D", "F"}

    # Placeholder heavy → lower score
    g_bad = DesignGraph(graph_id="g_bad", target=RenderTarget.REACT, root_id="root")
    g_bad.add_node(DesignNode(node_id="root", component_id="placeholder.page.container"))
    for i in range(6):
        nid = f"ph{i}"
        g_bad.add_node(DesignNode(
            node_id=nid, component_id="placeholder.organism.section",
            metadata={"needs_llm_fill": True},
        ))
        g_bad.link("root", "main", nid)
    report_bad = scorer.evaluate(g_bad, catalog, {"_product_type": "landing_page"})
    cleanliness = report_bad.get_axis(RadarAxis.CLEANLINESS)
    checks["placeholder_hurts_cleanliness"] = (
        cleanliness is not None and cleanliness.normalized_score < 0.5
    )

    # Ranking
    reports = scorer.rank_variants([g, g_bad], catalog, {"_product_type": "landing_page"})
    checks["clean_ranks_higher"] = reports[0].composite > reports[1].composite

    return checks


__all__ = [
    "RADAR_4D_VERSION", "RadarAxis",
    "AxisScore", "score_to_grade",
    "AxisScorer", "SpeedScorer", "FootprintScorer",
    "StabilityScorer", "CleanlinessScorer",
    "RadarWeights", "Radar4DReport", "Radar4DScorer",
    "EXPECTED_NODES_BY_PRODUCT",
    "radar_4d_sanity_check",
]
