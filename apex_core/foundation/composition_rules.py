"""
APEX FACTORY v6.0 - Foundation Extension
File: composition_rules.py

Mục đích: Tầng HỢP CHẤT của ontology UI. Thay thế "chạm/tổng/bóng" của
          ontology XSMB v5.0 bằng các luật kết hợp component trong khuôn.

Triết lý NT4 (Constrained Creativity):
    Mọi sáng tạo chỉ được phép trong khuôn ontology. Rule Engine là
    "tòa án Calvar" chặn mọi cấu trúc ngoài luật.

Các loại luật:
  1. ContainmentRule     - category nào chứa được category nào
  2. StackingRule        - z-index phải tuân layer order
  3. ResponsiveRule      - luật biến đổi theo breakpoint
  4. SemanticPairingRule - involution/orbit (light↔dark, LTR↔RTL)
  5. LayoutRatioRule     - luật tỷ lệ (8pt grid, golden ratio)
  6. UniquenessRule      - 1 page chỉ có 1 <main>, 1 <h1>
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from apex_core.foundation.ontology_ui import (
    Breakpoint,
    ComponentCatalog,
    ComponentCategory,
    ComponentSpec,
)
from apex_core.foundation.ui_ir import DesignGraph, DesignNode
from apex_core.legacy.foundation.principles import Principle, enforce_principle

# ============================================================
# 0. VERSION
# ============================================================

COMPOSITION_RULES_VERSION = "6.0.0"


# ============================================================
# 1. RULE BASE + RESULT
# ============================================================

class RuleSeverity(str, Enum):
    ERROR = "error"         # Graph invalid - không được render
    WARNING = "warning"     # Cho phép render nhưng Radar 4D trừ điểm
    INFO = "info"           # Chỉ ghi audit, không ảnh hưởng quyết định


@dataclass(frozen=True)
class RuleViolation:
    rule_id: str
    rule_title: str
    severity: RuleSeverity
    message: str
    affected_node_ids: Tuple[str, ...] = ()
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_title": self.rule_title,
            "severity": self.severity.value,
            "message": self.message,
            "affected_node_ids": list(self.affected_node_ids),
            "suggestion": self.suggestion,
        }


class CompositionRule(ABC):
    """Base class cho mọi luật kết hợp."""
    RULE_ID: str = "base"
    RULE_TITLE: str = "Base Rule"
    SEVERITY: RuleSeverity = RuleSeverity.ERROR

    @abstractmethod
    def check(
        self,
        graph: DesignGraph,
        catalog: ComponentCatalog,
    ) -> List[RuleViolation]:
        ...

    def _violation(
        self,
        message: str,
        affected: Sequence[str] = (),
        suggestion: str = "",
    ) -> RuleViolation:
        return RuleViolation(
            rule_id=self.RULE_ID,
            rule_title=self.RULE_TITLE,
            severity=self.SEVERITY,
            message=message,
            affected_node_ids=tuple(affected),
            suggestion=suggestion,
        )


# ============================================================
# 2. CONTAINMENT RULE (category containment)
# ============================================================

# Bảng chứa đựng chuẩn Atomic Design (khe dung sai rộng vừa phải):
#   Key = parent category
#   Value = set các category con được phép
DEFAULT_CONTAINMENT_MATRIX: Dict[ComponentCategory, FrozenSet[ComponentCategory]] = {
    ComponentCategory.PAGE: frozenset({
        ComponentCategory.TEMPLATE,
        ComponentCategory.ORGANISM,
        ComponentCategory.LAYOUT,
        ComponentCategory.PATTERN,
    }),
    ComponentCategory.TEMPLATE: frozenset({
        ComponentCategory.ORGANISM,
        ComponentCategory.LAYOUT,
        ComponentCategory.PATTERN,
        ComponentCategory.MOLECULE,
    }),
    ComponentCategory.ORGANISM: frozenset({
        ComponentCategory.ORGANISM,     # cho phép compose
        ComponentCategory.MOLECULE,
        ComponentCategory.ATOM,
        ComponentCategory.LAYOUT,
    }),
    ComponentCategory.MOLECULE: frozenset({
        ComponentCategory.MOLECULE,
        ComponentCategory.ATOM,
        ComponentCategory.LAYOUT,
    }),
    ComponentCategory.ATOM: frozenset({
        ComponentCategory.ATOM,         # chỉ atom của cùng loại (icon trong button)
    }),
    ComponentCategory.LAYOUT: frozenset({
        ComponentCategory.ATOM,
        ComponentCategory.MOLECULE,
        ComponentCategory.ORGANISM,
        ComponentCategory.LAYOUT,
    }),
    ComponentCategory.PATTERN: frozenset({
        ComponentCategory.ORGANISM,
        ComponentCategory.MOLECULE,
        ComponentCategory.LAYOUT,
    }),
}


class ContainmentRule(CompositionRule):
    """
    Category cha chỉ được chứa category con theo bảng DEFAULT_CONTAINMENT_MATRIX.
    Vi phạm điển hình: page lồng trong atom, button chứa navbar.
    """
    RULE_ID = "composition.containment"
    RULE_TITLE = "Atomic Design Containment"
    SEVERITY = RuleSeverity.ERROR

    def __init__(
        self,
        matrix: Optional[Dict[ComponentCategory, FrozenSet[ComponentCategory]]] = None,
    ):
        self._matrix = matrix or DEFAULT_CONTAINMENT_MATRIX

    @enforce_principle(Principle.NT4_CONSTRAINED_CREATIVITY)
    def check(self, graph, catalog) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        for parent_id, parent_node in graph.nodes.items():
            parent_spec = catalog.get(parent_node.component_id)
            if parent_spec is None:
                continue
            allowed = self._matrix.get(parent_spec.category, frozenset())
            for slot_name, child_ids in parent_node.children_by_slot.items():
                for child_id in child_ids:
                    child = graph.nodes.get(child_id)
                    if child is None:
                        continue
                    child_spec = catalog.get(child.component_id)
                    if child_spec is None:
                        continue
                    if child_spec.category not in allowed:
                        violations.append(self._violation(
                            message=(
                                f"{parent_spec.category.value} '{parent_spec.component_id}' "
                                f"không được chứa {child_spec.category.value} "
                                f"'{child_spec.component_id}' (slot='{slot_name}')"
                            ),
                            affected=[parent_id, child_id],
                            suggestion=(
                                f"Cho phép: {[c.value for c in allowed]}"
                            ),
                        ))
        return violations


# ============================================================
# 3. STACKING RULE (z-index layer order)
# ============================================================

# Layer order - cao hơn = nổi lên trên
Z_LAYER_ORDER: Tuple[str, ...] = (
    "background",    # 0
    "content",       # 1
    "floating",      # 2 (sticky header, FAB)
    "dropdown",      # 3
    "drawer",        # 4
    "modal",         # 5
    "toast",         # 6
    "tooltip",       # 7
    "loading",       # 8 (spinner toàn màn hình)
)

LAYER_TO_INDEX: Dict[str, int] = {name: i for i, name in enumerate(Z_LAYER_ORDER)}


class StackingRule(CompositionRule):
    """
    Component tag với layer nào phải có z-index đúng thứ tự.
    Node metadata có 'z_layer' string -> check index.
    """
    RULE_ID = "composition.stacking"
    RULE_TITLE = "Z-Index Layer Order"
    SEVERITY = RuleSeverity.WARNING

    def check(self, graph, catalog) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        # Thu thập (node_id, layer_name, z_value) từ metadata
        tagged: List[Tuple[str, str, Optional[int]]] = []
        for nid, node in graph.nodes.items():
            layer = node.metadata.get("z_layer")
            if not isinstance(layer, str):
                continue
            if layer not in LAYER_TO_INDEX:
                violations.append(self._violation(
                    message=f"Node {nid}: unknown z_layer '{layer}'",
                    affected=[nid],
                    suggestion=f"Allowed layers: {list(LAYER_TO_INDEX.keys())}",
                ))
                continue
            z_val = node.props.get("zIndex")
            if z_val is not None and not isinstance(z_val, int):
                violations.append(self._violation(
                    message=f"Node {nid}: zIndex không phải int ({z_val!r})",
                    affected=[nid],
                ))
                continue
            tagged.append((nid, layer, z_val))

        # Check: nếu 2 node có layer khác nhau thì zIndex phải theo thứ tự layer
        for i, (id_a, layer_a, z_a) in enumerate(tagged):
            for id_b, layer_b, z_b in tagged[i + 1:]:
                if z_a is None or z_b is None:
                    continue
                idx_a = LAYER_TO_INDEX[layer_a]
                idx_b = LAYER_TO_INDEX[layer_b]
                if idx_a < idx_b and z_a >= z_b:
                    violations.append(self._violation(
                        message=(
                            f"Node {id_a} (layer={layer_a}, z={z_a}) ≥ "
                            f"Node {id_b} (layer={layer_b}, z={z_b}) - "
                            f"sai thứ tự stacking"
                        ),
                        affected=[id_a, id_b],
                    ))
        return violations


# ============================================================
# 4. RESPONSIVE RULE (breakpoint coverage)
# ============================================================

class ResponsiveCoverageRule(CompositionRule):
    """
    Mọi organism/template/page phải có khai báo responsive cho ít nhất các
    breakpoint core. Tránh tình trạng dùng layout fixed cứng.
    """
    RULE_ID = "composition.responsive_coverage"
    RULE_TITLE = "Responsive Breakpoint Coverage"
    SEVERITY = RuleSeverity.WARNING

    REQUIRED_BREAKPOINTS: FrozenSet[Breakpoint] = frozenset({
        Breakpoint.SM, Breakpoint.MD, Breakpoint.LG,
    })

    REQUIRE_FOR_CATEGORIES: FrozenSet[ComponentCategory] = frozenset({
        ComponentCategory.PAGE,
        ComponentCategory.TEMPLATE,
        ComponentCategory.ORGANISM,
        ComponentCategory.PATTERN,
    })

    def check(self, graph, catalog) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        for nid, node in graph.nodes.items():
            spec = catalog.get(node.component_id)
            if spec is None:
                continue
            if spec.category not in self.REQUIRE_FOR_CATEGORIES:
                continue

            declared_bps: Set[Breakpoint] = set()
            # Từ component spec
            for rv in spec.responsive_variants:
                declared_bps.add(rv.breakpoint)
            # Từ node-level overrides
            for bp_str in node.responsive_overrides.keys():
                try:
                    declared_bps.add(Breakpoint(bp_str))
                except ValueError:
                    continue

            missing = self.REQUIRED_BREAKPOINTS - declared_bps
            if missing:
                violations.append(self._violation(
                    message=(
                        f"Node {nid} ({spec.component_id}): thiếu responsive cho "
                        f"{sorted(b.value for b in missing)}"
                    ),
                    affected=[nid],
                    suggestion="Bổ sung responsive_variants hoặc responsive_overrides",
                ))
        return violations


# ============================================================
# 5. SEMANTIC PAIRING RULE (involution: light↔dark, LTR↔RTL)
# ============================================================

@dataclass(frozen=True)
class PairingFamily:
    """1 family involution - tương đương 'shadow family' của ontology XSMB."""
    family_id: str
    title: str
    members: Tuple[str, ...]       # VD: ("light", "dark")
    is_involution: bool = True     # áp 2 lần = nguyên

    def partner_of(self, member: str) -> Optional[str]:
        if member not in self.members:
            return None
        if not self.is_involution or len(self.members) != 2:
            return None
        return self.members[1] if member == self.members[0] else self.members[0]


DEFAULT_PAIRING_FAMILIES: Tuple[PairingFamily, ...] = (
    PairingFamily(
        family_id="theme.light_dark",
        title="Light ↔ Dark Theme",
        members=("light", "dark"),
    ),
    PairingFamily(
        family_id="direction.ltr_rtl",
        title="LTR ↔ RTL",
        members=("ltr", "rtl"),
    ),
    PairingFamily(
        family_id="density.compact_comfortable",
        title="Compact ↔ Comfortable",
        members=("compact", "comfortable"),
    ),
)


class SemanticPairingRule(CompositionRule):
    """
    Nếu graph khai báo có theme 'light' thì PHẢI có support cho 'dark'
    (involution). Giống logic involution của bóng âm/dương cũ.
    """
    RULE_ID = "composition.semantic_pairing"
    RULE_TITLE = "Semantic Pairing Involution"
    SEVERITY = RuleSeverity.WARNING

    def __init__(
        self,
        families: Optional[Sequence[PairingFamily]] = None,
        enforce_family_ids: Optional[Sequence[str]] = None,
    ):
        self._families = {f.family_id: f for f in (families or DEFAULT_PAIRING_FAMILIES)}
        self._enforce = set(enforce_family_ids or ["theme.light_dark"])

    def check(self, graph, catalog) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        declared = graph.metadata.get("semantic_pairs", {})
        if not isinstance(declared, dict):
            return violations

        for family_id in self._enforce:
            family = self._families.get(family_id)
            if family is None:
                continue
            declared_members = declared.get(family_id, [])
            if not declared_members:
                continue
            declared_set = set(declared_members)
            # Involution: nếu có 1 member thì phải có partner
            for m in declared_members:
                partner = family.partner_of(m)
                if partner is None:
                    continue
                if partner not in declared_set:
                    violations.append(self._violation(
                        message=(
                            f"Family '{family.title}': đã khai báo '{m}' "
                            f"nhưng thiếu involution partner '{partner}'"
                        ),
                        suggestion=f"Thêm '{partner}' vào metadata.semantic_pairs['{family_id}']",
                    ))
        return violations


# ============================================================
# 6. LAYOUT RATIO RULE (8pt grid)
# ============================================================

class EightPtGridRule(CompositionRule):
    """
    Mọi spacing override phải là bội số 0.25rem (4px) - 8pt grid thân thiện
    cho visual rhythm.
    """
    RULE_ID = "composition.eight_pt_grid"
    RULE_TITLE = "8pt Grid Discipline"
    SEVERITY = RuleSeverity.INFO

    GRID_UNIT_REM: float = 0.25

    def check(self, graph, catalog) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        for nid, node in graph.nodes.items():
            for prop_name, value in node.props.items():
                if not prop_name.startswith(("padding", "margin", "gap")):
                    continue
                if not isinstance(value, (int, float)):
                    continue
                rem = float(value)
                # Cho phép 0 và bội của GRID_UNIT_REM
                if rem == 0:
                    continue
                remainder = round(rem / self.GRID_UNIT_REM, 4) % 1
                if not (remainder < 1e-4 or remainder > 1 - 1e-4):
                    violations.append(self._violation(
                        message=(
                            f"Node {nid} prop '{prop_name}'={rem}rem "
                            f"không phải bội của {self.GRID_UNIT_REM}rem"
                        ),
                        affected=[nid],
                        suggestion=f"Làm tròn về {round(rem / self.GRID_UNIT_REM) * self.GRID_UNIT_REM}",
                    ))
        return violations


# ============================================================
# 7. UNIQUENESS RULE (1 <main>, 1 <h1>)
# ============================================================

class LandmarkUniquenessRule(CompositionRule):
    """
    HTML landmarks: chỉ được có 1 <main>, 1 <h1> cho mỗi page.
    Accessibility best practice.
    """
    RULE_ID = "composition.landmark_uniqueness"
    RULE_TITLE = "Landmark Uniqueness (A11y)"
    SEVERITY = RuleSeverity.ERROR

    UNIQUE_ROLES: FrozenSet[str] = frozenset({"main", "heading_h1"})

    def check(self, graph, catalog) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        role_counts: Dict[str, List[str]] = {}

        for nid, node in graph.nodes.items():
            spec = catalog.get(node.component_id)
            if spec is None:
                continue
            role_value = spec.a11y.role.value
            # Heading đặc biệt: check level
            if role_value == "heading":
                level = node.props.get("level") or node.metadata.get("heading_level")
                if level == 1:
                    role_counts.setdefault("heading_h1", []).append(nid)
            if role_value == "main":
                role_counts.setdefault("main", []).append(nid)

        for role, node_ids in role_counts.items():
            if role in self.UNIQUE_ROLES and len(node_ids) > 1:
                violations.append(self._violation(
                    message=f"Role '{role}' xuất hiện {len(node_ids)} lần - phải unique",
                    affected=node_ids,
                    suggestion=f"Chỉ giữ 1 node với role '{role}' trên mỗi page",
                ))
        return violations


# ============================================================
# 8. RULE ENGINE
# ============================================================

@dataclass
class RuleEngineReport:
    total_rules_run: int
    total_violations: int
    by_severity: Dict[str, int]
    violations: List[RuleViolation]

    @property
    def is_graph_renderable(self) -> bool:
        """Không có ERROR → có thể render (kể cả còn WARNING)."""
        return self.by_severity.get(RuleSeverity.ERROR.value, 0) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rules_run": self.total_rules_run,
            "total_violations": self.total_violations,
            "by_severity": dict(self.by_severity),
            "is_renderable": self.is_graph_renderable,
            "violations": [v.to_dict() for v in self.violations],
        }


class RuleEngine:
    """
    Chạy một tập luật lên DesignGraph, aggregate kết quả.
    Mặc định load 6 luật core - có thể hot-plug thêm (NT10).
    """

    def __init__(self, rules: Optional[Sequence[CompositionRule]] = None):
        self._rules: List[CompositionRule] = list(rules) if rules else self._default_rules()

    @staticmethod
    def _default_rules() -> List[CompositionRule]:
        return [
            ContainmentRule(),
            StackingRule(),
            ResponsiveCoverageRule(),
            SemanticPairingRule(),
            EightPtGridRule(),
            LandmarkUniquenessRule(),
        ]

    def add_rule(self, rule: CompositionRule) -> None:
        """NT10 hot-plug."""
        self._rules.append(rule)

    @enforce_principle(Principle.NT4_CONSTRAINED_CREATIVITY)
    def evaluate(
        self,
        graph: DesignGraph,
        catalog: ComponentCatalog,
    ) -> RuleEngineReport:
        all_violations: List[RuleViolation] = []
        for rule in self._rules:
            try:
                all_violations.extend(rule.check(graph, catalog))
            except Exception as exc:
                all_violations.append(RuleViolation(
                    rule_id=rule.RULE_ID,
                    rule_title=rule.RULE_TITLE,
                    severity=RuleSeverity.ERROR,
                    message=f"Rule crashed: {type(exc).__name__}: {exc}",
                ))

        by_sev: Dict[str, int] = {}
        for v in all_violations:
            by_sev[v.severity.value] = by_sev.get(v.severity.value, 0) + 1

        return RuleEngineReport(
            total_rules_run=len(self._rules),
            total_violations=len(all_violations),
            by_severity=by_sev,
            violations=all_violations,
        )


# ============================================================
# 9. SANITY CHECK
# ============================================================

def composition_rules_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ontology_ui import (
        A11yContract,
        A11yRole,
        ComponentState,
        PropSchema,
        RenderTarget,
        SlotSchema,
    )
    from apex_core.foundation.ontology_ui import (
        ComponentCategory as Cat,
    )

    checks: Dict[str, bool] = {}

    # Setup catalog với 2 component: atom.button + page.home
    catalog = ComponentCatalog()

    btn = ComponentSpec(
        component_id="atom.button",
        label="Button",
        category=Cat.ATOM,
        prop_schema=(PropSchema("label", "string", required=True),),
        slots=(),
        states=(ComponentState.DEFAULT,),
        a11y=A11yContract(
            role=A11yRole.BUTTON,
            keyboard_map=(("Enter", "activate"),),
        ),
        design_tokens_used=(),
        dependencies=(),
        render_targets=(RenderTarget.REACT,),
    )
    page = ComponentSpec(
        component_id="page.home",
        label="Home Page",
        category=Cat.PAGE,
        prop_schema=(),
        slots=(SlotSchema(name="main"),),
        states=(ComponentState.DEFAULT,),
        a11y=A11yContract(role=A11yRole.MAIN),
        design_tokens_used=(),
        dependencies=(),
        render_targets=(RenderTarget.REACT,),
    )
    catalog.register(btn)
    catalog.register(page)

    # Case 1: Containment vi phạm - atom chứa page
    g_bad = DesignGraph(
        graph_id="g_bad",
        target=RenderTarget.REACT,
        root_id="n_btn",
    )
    g_bad.add_node(DesignNode(node_id="n_btn", component_id="atom.button",
                              props={"label": "Click"}))
    # Intentional violation - atom chứa page
    g_bad.add_node(DesignNode(node_id="n_page", component_id="page.home"))
    g_bad.nodes["n_btn"].children_by_slot["default"] = ["n_page"]

    engine = RuleEngine([ContainmentRule()])
    rep_bad = engine.evaluate(g_bad, catalog)
    checks["containment_catches_violation"] = rep_bad.total_violations >= 1

    # Case 2: Graph hợp lệ
    g_good = DesignGraph(
        graph_id="g_good",
        target=RenderTarget.REACT,
        root_id="n_page",
    )
    g_good.add_node(DesignNode(node_id="n_page", component_id="page.home"))
    rep_good = engine.evaluate(g_good, catalog)
    checks["good_graph_no_violation"] = rep_good.total_violations == 0

    # Case 3: Semantic pairing - khai báo light thiếu dark
    g_pair = DesignGraph(
        graph_id="g_pair",
        target=RenderTarget.REACT,
        root_id="n_page",
        metadata={"semantic_pairs": {"theme.light_dark": ["light"]}},
    )
    g_pair.add_node(DesignNode(node_id="n_page", component_id="page.home"))
    engine2 = RuleEngine([SemanticPairingRule()])
    rep_pair = engine2.evaluate(g_pair, catalog)
    checks["pairing_involution_enforced"] = rep_pair.total_violations >= 1

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "COMPOSITION_RULES_VERSION",
    "RuleSeverity",
    "RuleViolation",
    "CompositionRule",
    "DEFAULT_CONTAINMENT_MATRIX",
    "ContainmentRule",
    "Z_LAYER_ORDER",
    "LAYER_TO_INDEX",
    "StackingRule",
    "ResponsiveCoverageRule",
    "PairingFamily",
    "DEFAULT_PAIRING_FAMILIES",
    "SemanticPairingRule",
    "EightPtGridRule",
    "LandmarkUniquenessRule",
    "RuleEngineReport",
    "RuleEngine",
    "composition_rules_sanity_check",
]
