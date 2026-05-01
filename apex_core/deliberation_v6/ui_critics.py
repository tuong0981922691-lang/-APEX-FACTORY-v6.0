"""
APEX FACTORY v6.0 - Deliberation Layer (v6)
File: ui_critics.py

Mục đích: 7 CRITIC MỚI cho Round Table (thay 7 critic XSMB cũ).
    Chạy SAU Radar 4D, TRƯỚC quality_gate. Output: CriticVerdict.

    C1 - UXHeuristicCritic       : Nielsen subset (affordance, feedback...)
    C2 - PerformanceCritic       : Core Web Vitals thresholds
    C3 - AccessibilityCritic     : WCAG 2.2 AA
    C4 - SEOCritic               : semantic HTML + meta
    C5 - SecurityCritic          : XSS / CSP / leak
    C6 - CodeSmellCritic         : DAG anti-patterns
    C7 - BrandConsistencyCritic  : token drift

Triết lý NT9 (Round Table = Critic, KHÔNG sáng tạo):
    Mọi critic CHỈ tìm lỗi, đề xuất sửa. KHÔNG tạo node mới.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from apex_core.deliberation_v6.radar_4d import Radar4DReport, RadarAxis
from apex_core.foundation.ontology_ui import (
    A11yRole,
    ComponentCatalog,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.ui_ir import DesignGraph, DesignNode

# ============================================================
# 0. VERSION
# ============================================================

UI_CRITICS_VERSION = "6.0.0"


# ============================================================
# 1. CRITIC VERDICT SCHEMA
# ============================================================

class CriticVerdictStatus(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class UIFinding:
    title: str
    message: str
    affected_node_ids: Tuple[str, ...] = ()
    severity: str = "warning"       # "error" | "warning" | "info"
    suggestion: str = ""


@dataclass(frozen=True)
class UICriticVerdict:
    critic_id: str
    critic_name: str
    status: CriticVerdictStatus
    concern_level: float            # 0..1 (1 = rất đáng lo)
    findings: Tuple[UIFinding, ...]
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "critic_id": self.critic_id,
            "critic_name": self.critic_name,
            "status": self.status.value,
            "concern_level": round(self.concern_level, 4),
            "reasoning": self.reasoning,
            "findings": [
                {
                    "title": f.title,
                    "message": f.message,
                    "affected_node_ids": list(f.affected_node_ids),
                    "severity": f.severity,
                    "suggestion": f.suggestion,
                }
                for f in self.findings
            ],
        }


# ============================================================
# 2. CRITIC BASE
# ============================================================

@dataclass(frozen=True)
class CriticInput:
    graph: DesignGraph
    catalog: ComponentCatalog
    radar_report: Optional[Radar4DReport] = None
    brief_constraints: Mapping[str, Any] = field(default_factory=dict)
    brief_tone: Tuple[str, ...] = ()
    brief_product_type: str = ""


class UICritic(ABC):
    CRITIC_ID: str = "C0"
    CRITIC_NAME: str = "Base"

    @abstractmethod
    def review(self, inp: CriticInput) -> UICriticVerdict:
        ...

    def _verdict(
        self,
        status: CriticVerdictStatus,
        concern: float,
        findings: Sequence[UIFinding],
        reasoning: str,
    ) -> UICriticVerdict:
        return UICriticVerdict(
            critic_id=self.CRITIC_ID,
            critic_name=self.CRITIC_NAME,
            status=status,
            concern_level=max(0.0, min(1.0, concern)),
            findings=tuple(findings),
            reasoning=reasoning,
        )


# ============================================================
# 3. C1 - UX HEURISTIC CRITIC (Nielsen subset)
# ============================================================

class UXHeuristicCritic(UICritic):
    CRITIC_ID = "C1"
    CRITIC_NAME = "UXHeuristic"

    # Feature quan trọng phải "đủ affordance" - có CTA rõ cho landing
    CTA_REQUIRED_PRODUCT_TYPES: FrozenSet[str] = frozenset({
        "landing_page", "ecommerce", "saas_app",
    })

    def review(self, inp):
        findings: List[UIFinding] = []

        # H2.1 - có CTA không?
        if inp.brief_product_type in self.CTA_REQUIRED_PRODUCT_TYPES:
            has_cta = any(
                n.metadata.get("feature_id") == "cta" or "cta" in n.component_id.lower()
                or "button.primary" in n.component_id.lower()
                for n in inp.graph.nodes.values()
            )
            if not has_cta:
                findings.append(UIFinding(
                    title="Missing Primary CTA",
                    message=f"{inp.brief_product_type} không có CTA rõ ràng.",
                    severity="error",
                    suggestion="Thêm atom.button.primary ở hero hoặc pricing.",
                ))

        # H2.2 - quá nhiều CTA cạnh tranh?
        cta_count = sum(
            1 for n in inp.graph.nodes.values()
            if n.metadata.get("feature_id") == "cta"
        )
        if cta_count > 4:
            findings.append(UIFinding(
                title="CTA Overload",
                message=f"Có {cta_count} CTA - nguy cơ phân tán attention.",
                severity="warning",
                suggestion="Ưu tiên 1 CTA chính + 1-2 CTA phụ.",
            ))

        # H2.3 - visibility of system status: có feedback cho action?
        interactive_count = sum(
            1 for n in inp.graph.nodes.values()
            if n.event_handlers
        )
        loading_or_state = sum(
            1 for n in inp.graph.nodes.values()
            if any(s in ("loading", "error", "success") for s in [str(n.metadata.get("state", ""))])
        )
        if interactive_count > 3 and loading_or_state == 0:
            findings.append(UIFinding(
                title="No System Feedback",
                message="Nhiều phần tử tương tác nhưng không có state feedback.",
                severity="warning",
                suggestion="Thêm loading/success state cho form và button async.",
            ))

        # Decide
        errors = sum(1 for f in findings if f.severity == "error")
        warnings_n = sum(1 for f in findings if f.severity == "warning")
        concern = min(1.0, errors * 0.5 + warnings_n * 0.2)
        if errors > 0:
            status = CriticVerdictStatus.REJECT
        elif warnings_n > 0:
            status = CriticVerdictStatus.NEUTRAL
        else:
            status = CriticVerdictStatus.ACCEPT
        return self._verdict(
            status=status, concern=concern, findings=findings,
            reasoning=f"UX: {errors} err, {warnings_n} warn",
        )


# ============================================================
# 4. C2 - PERFORMANCE CRITIC
# ============================================================

class PerformanceCritic(UICritic):
    CRITIC_ID = "C2"
    CRITIC_NAME = "Performance"

    def review(self, inp):
        findings: List[UIFinding] = []
        if inp.radar_report is None:
            return self._verdict(
                CriticVerdictStatus.NEUTRAL, 0.0, findings,
                "No Radar report - skipping perf review",
            )

        speed = inp.radar_report.get_axis(RadarAxis.SPEED)
        footprint = inp.radar_report.get_axis(RadarAxis.FOOTPRINT)

        if speed and speed.normalized_score < 0.5:
            findings.append(UIFinding(
                title="Speed Below Threshold",
                message=(
                    f"Estimated LCP {speed.breakdown.get('estimated_lcp_ms', 0):.0f}ms, "
                    f"score {speed.normalized_score:.2f}"
                ),
                severity="error" if speed.normalized_score < 0.3 else "warning",
                suggestion="Giảm animation, lazy-load component dưới fold.",
            ))

        if footprint and footprint.normalized_score < 0.5:
            findings.append(UIFinding(
                title="Bundle Too Heavy",
                message=(
                    f"Estimated bundle {footprint.raw_value}kb, "
                    f"target {footprint.breakdown.get('target_bundle_kb', 0)}kb"
                ),
                severity="error" if footprint.normalized_score < 0.3 else "warning",
                suggestion="Code-split và dynamic import cho feature không-critical.",
            ))

        concern = 1.0 - min(
            speed.normalized_score if speed else 1.0,
            footprint.normalized_score if footprint else 1.0,
        )
        status = (
            CriticVerdictStatus.REJECT if concern > 0.6
            else CriticVerdictStatus.NEUTRAL if concern > 0.3
            else CriticVerdictStatus.ACCEPT
        )
        return self._verdict(
            status=status, concern=concern, findings=findings,
            reasoning=f"Speed={speed.grade if speed else '?'}, Footprint={footprint.grade if footprint else '?'}",
        )


# ============================================================
# 5. C3 - ACCESSIBILITY CRITIC (NT12 enforcement)
# ============================================================

class AccessibilityCritic(UICritic):
    CRITIC_ID = "C3"
    CRITIC_NAME = "Accessibility"

    @enforce_principle_v6(PrincipleV6.NT12_ACCESSIBILITY_NON_NEGOTIABLE)
    def review(self, inp):
        findings: List[UIFinding] = []
        main_count = 0
        h1_count = 0
        no_role_interactive: List[str] = []
        missing_aria_label: List[str] = []

        for nid, n in inp.graph.nodes.items():
            spec = inp.catalog.get(n.component_id)
            if spec is None:
                # Placeholder - không có spec - flag as risk
                if n.component_id.startswith("placeholder."):
                    findings.append(UIFinding(
                        title="Placeholder A11y Unknown",
                        message=f"Node {nid} là placeholder - không có a11y contract.",
                        affected_node_ids=(nid,),
                        severity="warning",
                        suggestion="Fill placeholder trước khi publish.",
                    ))
                continue

            role = spec.a11y.role
            if role == A11yRole.MAIN:
                main_count += 1
            if role == A11yRole.HEADING and (n.props.get("level") == 1 or n.metadata.get("heading_level") == 1):
                h1_count += 1
            # Button/Link phải có keyboard handler
            if role in (A11yRole.BUTTON, A11yRole.LINK) and not spec.a11y.keyboard_map:
                no_role_interactive.append(nid)
            if role == A11yRole.IMG and "aria-label" not in spec.a11y.required_aria:
                missing_aria_label.append(nid)

        if main_count > 1:
            findings.append(UIFinding(
                title="Multiple <main>",
                message=f"{main_count} landmark main - vi phạm WCAG (duy nhất).",
                severity="error",
                suggestion="Gộp thành 1 main, các phần khác dùng section/region.",
            ))
        if h1_count > 1:
            findings.append(UIFinding(
                title="Multiple H1",
                message=f"{h1_count} h1 - vi phạm best practice.",
                severity="error",
                suggestion="Chỉ 1 h1 per page, các heading khác dùng h2-h6.",
            ))

        if no_role_interactive:
            findings.append(UIFinding(
                title="Interactive Without Keyboard",
                message=f"{len(no_role_interactive)} node interactive thiếu keyboard_map.",
                affected_node_ids=tuple(no_role_interactive[:5]),
                severity="error",
                suggestion="ComponentSpec.a11y.keyboard_map bắt buộc cho button/link.",
            ))
        if missing_aria_label:
            findings.append(UIFinding(
                title="IMG Missing aria-label",
                affected_node_ids=tuple(missing_aria_label[:5]),
                message=f"{len(missing_aria_label)} IMG không có aria-label.",
                severity="error",
            ))

        errors = sum(1 for f in findings if f.severity == "error")
        warnings_n = sum(1 for f in findings if f.severity == "warning")
        concern = min(1.0, errors * 0.35 + warnings_n * 0.15)
        status = (
            CriticVerdictStatus.REJECT if errors > 0
            else CriticVerdictStatus.NEUTRAL if warnings_n > 0
            else CriticVerdictStatus.ACCEPT
        )
        return self._verdict(
            status=status, concern=concern, findings=findings,
            reasoning=f"A11y errors={errors}, warnings={warnings_n}",
        )


# ============================================================
# 6. C4 - SEO CRITIC
# ============================================================

class SEOCritic(UICritic):
    CRITIC_ID = "C4"
    CRITIC_NAME = "SEO"

    SEO_REQUIRED_PRODUCTS: FrozenSet[str] = frozenset({
        "landing_page", "blog", "ecommerce", "portfolio",
    })

    def review(self, inp):
        if inp.brief_product_type not in self.SEO_REQUIRED_PRODUCTS:
            return self._verdict(
                CriticVerdictStatus.NEUTRAL, 0.0, (),
                "Product type không yêu cầu SEO nghiêm ngặt",
            )

        findings: List[UIFinding] = []
        has_main = False
        has_h1 = False
        has_footer = False
        has_meta = inp.graph.metadata.get("seo_meta") is not None

        for n in inp.graph.nodes.values():
            spec = inp.catalog.get(n.component_id)
            if spec is None:
                continue
            if spec.a11y.role == A11yRole.MAIN:
                has_main = True
            if spec.a11y.role == A11yRole.HEADING and (n.props.get("level") == 1 or n.metadata.get("heading_level") == 1):
                has_h1 = True
            if spec.a11y.role == A11yRole.FOOTER:
                has_footer = True

        if not has_main:
            findings.append(UIFinding("No <main>", "Page thiếu landmark main.", severity="error"))
        if not has_h1:
            findings.append(UIFinding("No <h1>", "Page thiếu h1 - kém SEO.", severity="error"))
        if not has_footer:
            findings.append(UIFinding("No <footer>", "Page thiếu footer.", severity="warning"))
        if not has_meta:
            findings.append(UIFinding(
                "Missing SEO meta",
                "graph.metadata.seo_meta chưa có - thiếu title/description/og.",
                severity="warning",
                suggestion="Thêm metadata.seo_meta = {title, description, og_image, ...}",
            ))

        errors = sum(1 for f in findings if f.severity == "error")
        warnings_n = sum(1 for f in findings if f.severity == "warning")
        concern = min(1.0, errors * 0.3 + warnings_n * 0.15)
        status = (
            CriticVerdictStatus.REJECT if errors > 0
            else CriticVerdictStatus.NEUTRAL if warnings_n > 0
            else CriticVerdictStatus.ACCEPT
        )
        return self._verdict(status, concern, findings, f"SEO errors={errors}, warnings={warnings_n}")


# ============================================================
# 7. C5 - SECURITY CRITIC
# ============================================================

class SecurityCritic(UICritic):
    CRITIC_ID = "C5"
    CRITIC_NAME = "Security"

    # Props nghi ngờ chứa secret
    SUSPICIOUS_PROP_NAMES: FrozenSet[str] = frozenset({
        "apiKey", "api_key", "secret", "password", "token", "private_key",
    })
    # Pattern nghi ngờ XSS
    XSS_PROP_NAMES: FrozenSet[str] = frozenset({
        "dangerouslySetInnerHTML", "innerHTML", "__html",
    })

    def review(self, inp):
        findings: List[UIFinding] = []

        for nid, n in inp.graph.nodes.items():
            # 1. Hardcoded secret in props
            for prop_name, prop_value in n.props.items():
                if prop_name in self.SUSPICIOUS_PROP_NAMES and isinstance(prop_value, str) and len(prop_value) > 0:
                    findings.append(UIFinding(
                        title="Hardcoded Secret",
                        message=f"Node {nid} có prop '{prop_name}' với giá trị inline.",
                        affected_node_ids=(nid,),
                        severity="error",
                        suggestion="Dùng env var / data binding thay vì hardcode.",
                    ))
                if prop_name in self.XSS_PROP_NAMES:
                    findings.append(UIFinding(
                        title="XSS Risk",
                        message=f"Node {nid} dùng prop XSS-prone '{prop_name}'.",
                        affected_node_ids=(nid,),
                        severity="error",
                        suggestion="Dùng sanitizer (DOMPurify) hoặc component safe.",
                    ))

            # 2. External URL in event handler = tracking pixel risk
            for ev_name, handler in n.event_handlers.items():
                if isinstance(handler, str) and handler.startswith("http"):
                    findings.append(UIFinding(
                        title="External Handler URL",
                        message=f"Node {nid}.{ev_name} trỏ URL ngoài: {handler[:60]}",
                        affected_node_ids=(nid,),
                        severity="warning",
                    ))

        # 3. CSP meta declared?
        if inp.graph.metadata.get("csp_declared") is None and inp.brief_product_type != "mobile_app":
            findings.append(UIFinding(
                title="No CSP",
                message="graph.metadata.csp_declared = None - thiếu Content-Security-Policy.",
                severity="warning",
                suggestion="Khai báo CSP ở emitter stage.",
            ))

        errors = sum(1 for f in findings if f.severity == "error")
        warnings_n = sum(1 for f in findings if f.severity == "warning")
        concern = min(1.0, errors * 0.5 + warnings_n * 0.15)
        status = (
            CriticVerdictStatus.REJECT if errors > 0
            else CriticVerdictStatus.NEUTRAL if warnings_n > 0
            else CriticVerdictStatus.ACCEPT
        )
        return self._verdict(status, concern, findings, f"Security errors={errors}")


# ============================================================
# 8. C6 - CODE SMELL CRITIC
# ============================================================

class CodeSmellCritic(UICritic):
    CRITIC_ID = "C6"
    CRITIC_NAME = "CodeSmell"

    def review(self, inp):
        findings: List[UIFinding] = []
        g = inp.graph

        # God node: 1 node có quá nhiều children
        for nid, n in g.nodes.items():
            total_children = sum(len(c) for c in n.children_by_slot.values())
            if total_children > 15:
                findings.append(UIFinding(
                    title="God Node",
                    message=f"Node {nid} chứa {total_children} child - nên split.",
                    affected_node_ids=(nid,),
                    severity="warning",
                    suggestion="Tách thành sub-organism.",
                ))

        # Deep nesting
        max_depth = max((d for d, _ in g.walk()), default=0)
        if max_depth > 7:
            findings.append(UIFinding(
                title="Excessive Nesting",
                message=f"Depth {max_depth} > 7 - khó maintain.",
                severity="warning",
                suggestion="Flatten với composition pattern.",
            ))

        # Dead branch: nodes không link được vào tree (orphan)
        reachable = {n.node_id for _, n in g.walk()}
        orphans = set(g.nodes.keys()) - reachable
        if orphans:
            findings.append(UIFinding(
                title="Orphan Nodes",
                message=f"{len(orphans)} node không reachable từ root.",
                affected_node_ids=tuple(sorted(orphans))[:5],
                severity="error",
                suggestion="Xóa hoặc link lại.",
            ))

        # Duplicate component in same parent slot
        for nid, n in g.nodes.items():
            for slot, child_ids in n.children_by_slot.items():
                comp_counts: Dict[str, int] = {}
                for cid in child_ids:
                    child = g.nodes.get(cid)
                    if child:
                        comp_counts[child.component_id] = comp_counts.get(child.component_id, 0) + 1
                for comp, cnt in comp_counts.items():
                    if cnt >= 3:
                        findings.append(UIFinding(
                            title="Repeated Child",
                            message=f"Slot {nid}.{slot} có {cnt} lần {comp} - có thể dùng list renderer.",
                            affected_node_ids=(nid,),
                            severity="info",
                            suggestion="Bind 1 node vào data source dạng array.",
                        ))

        errors = sum(1 for f in findings if f.severity == "error")
        warnings_n = sum(1 for f in findings if f.severity == "warning")
        concern = min(1.0, errors * 0.3 + warnings_n * 0.15)
        status = (
            CriticVerdictStatus.REJECT if errors > 0
            else CriticVerdictStatus.NEUTRAL if warnings_n > 0
            else CriticVerdictStatus.ACCEPT
        )
        return self._verdict(status, concern, findings, f"Smell errors={errors}")


# ============================================================
# 9. C7 - BRAND CONSISTENCY CRITIC (NT11 enforcement)
# ============================================================

class BrandConsistencyCritic(UICritic):
    CRITIC_ID = "C7"
    CRITIC_NAME = "BrandConsistency"

    @enforce_principle_v6(PrincipleV6.NT11_DESIGN_SYSTEM_INTEGRITY)
    def review(self, inp):
        findings: List[UIFinding] = []

        # 1. Các node có style_overrides trực tiếp (vi phạm token-first)
        hardcoded_override_count = 0
        offenders: List[str] = []
        for nid, n in inp.graph.nodes.items():
            if n.style_overrides:
                hardcoded_override_count += len(n.style_overrides)
                offenders.append(nid)

        if hardcoded_override_count > 5:
            findings.append(UIFinding(
                title="Style Drift",
                message=f"{hardcoded_override_count} style_override không qua token.",
                affected_node_ids=tuple(offenders[:5]),
                severity="warning",
                suggestion="Đưa override thành token mới và register vào TokenRegistry.",
            ))

        # 2. Components from different "brand families" mixed
        brand_prefixes: Dict[str, int] = {}
        for n in inp.graph.nodes.values():
            # Component_id như "organism.navbar.v2" → prefix "organism.navbar"
            parts = n.component_id.split(".")
            if len(parts) >= 2:
                prefix = ".".join(parts[:2])
                brand_prefixes[prefix] = brand_prefixes.get(prefix, 0) + 1

        if len(brand_prefixes) > 12:
            findings.append(UIFinding(
                title="Too Many Component Families",
                message=f"{len(brand_prefixes)} families khác nhau - nguy cơ visual inconsistency.",
                severity="info",
                suggestion="Limit 7-10 family chính.",
            ))

        # 3. Tone drift: theme khai báo vs component density
        declared_theme = inp.graph.metadata.get("variant_strategy", "")
        if "bold" in declared_theme.lower() and not any(
            n.metadata.get("has_animation") for n in inp.graph.nodes.values()
        ):
            findings.append(UIFinding(
                title="Tone Drift",
                message="Variant 'bold' nhưng không có animation node nào.",
                severity="info",
                suggestion="Bold thường cần motion/contrast layer.",
            ))

        warnings_n = sum(1 for f in findings if f.severity == "warning")
        concern = min(1.0, warnings_n * 0.25)
        status = (
            CriticVerdictStatus.NEUTRAL if warnings_n > 0
            else CriticVerdictStatus.ACCEPT
        )
        return self._verdict(status, concern, findings, f"Brand warnings={warnings_n}")


# ============================================================
# 10. ROUND TABLE ORCHESTRATOR (v6 - dùng 7 critic mới)
# ============================================================

DEFAULT_UI_CRITICS: Tuple[UICritic, ...] = (
    UXHeuristicCritic(),
    PerformanceCritic(),
    AccessibilityCritic(),
    SEOCritic(),
    SecurityCritic(),
    CodeSmellCritic(),
    BrandConsistencyCritic(),
)


@dataclass
class RoundTableV6Report:
    graph_id: str
    verdicts: List[UICriticVerdict]
    accept_count: int
    reject_count: int
    neutral_count: int
    avg_concern: float
    overall_recommendation: str         # "approve" | "revise" | "reject"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "verdicts": [v.to_dict() for v in self.verdicts],
            "accept_count": self.accept_count,
            "reject_count": self.reject_count,
            "neutral_count": self.neutral_count,
            "avg_concern": round(self.avg_concern, 4),
            "overall_recommendation": self.overall_recommendation,
        }


class RoundTableV6:
    def __init__(self, critics: Optional[Sequence[UICritic]] = None):
        self._critics: List[UICritic] = list(critics or DEFAULT_UI_CRITICS)

    def add_critic(self, critic: UICritic) -> None:
        self._critics.append(critic)

    @enforce_principle_v6(PrincipleV6.NT9_ROUND_TABLE_IS_CRITIC)
    def deliberate(self, inp: CriticInput) -> RoundTableV6Report:
        verdicts: List[UICriticVerdict] = []
        for critic in self._critics:
            try:
                verdicts.append(critic.review(inp))
            except Exception as e:
                verdicts.append(UICriticVerdict(
                    critic_id=critic.CRITIC_ID,
                    critic_name=critic.CRITIC_NAME,
                    status=CriticVerdictStatus.NEUTRAL,
                    concern_level=0.5,
                    findings=(UIFinding(
                        title="Critic Crash",
                        message=f"{type(e).__name__}: {e}",
                        severity="warning",
                    ),),
                    reasoning="critic_crash_safe_fallback",
                ))

        accept = sum(1 for v in verdicts if v.status == CriticVerdictStatus.ACCEPT)
        reject = sum(1 for v in verdicts if v.status == CriticVerdictStatus.REJECT)
        neutral = sum(1 for v in verdicts if v.status == CriticVerdictStatus.NEUTRAL)
        avg_concern = (
            sum(v.concern_level for v in verdicts) / len(verdicts) if verdicts else 0.0
        )

        # Overall rule
        if reject >= 3 or avg_concern > 0.65:
            recommendation = "reject"
        elif reject >= 1 or neutral >= 3:
            recommendation = "revise"
        else:
            recommendation = "approve"

        return RoundTableV6Report(
            graph_id=inp.graph.graph_id,
            verdicts=verdicts,
            accept_count=accept,
            reject_count=reject,
            neutral_count=neutral,
            avg_concern=avg_concern,
            overall_recommendation=recommendation,
        )


# ============================================================
# 11. SANITY CHECK
# ============================================================

def ui_critics_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ui_ir import RenderTarget
    checks: Dict[str, bool] = {}

    # Build graph bình thường - có navbar, hero, cta, footer
    g = DesignGraph(graph_id="g_ok", target=RenderTarget.REACT, root_id="root")
    g.add_node(DesignNode(node_id="root", component_id="page.landing"))
    g.add_node(DesignNode(node_id="nav", component_id="organism.navbar", metadata={"feature_id": "navbar"}))
    g.add_node(DesignNode(node_id="hero", component_id="organism.hero", metadata={"feature_id": "hero"}))
    g.add_node(DesignNode(node_id="cta", component_id="atom.button.primary", metadata={"feature_id": "cta"}))
    g.add_node(DesignNode(node_id="foot", component_id="organism.footer", metadata={"feature_id": "footer"}))
    g.link("root", "main", "nav")
    g.link("root", "main", "hero")
    g.link("root", "main", "cta")
    g.link("root", "main", "foot")

    catalog = ComponentCatalog()
    rt = RoundTableV6()
    inp = CriticInput(
        graph=g, catalog=catalog, radar_report=None,
        brief_product_type="landing_page",
    )
    report = rt.deliberate(inp)
    checks["seven_verdicts"] = len(report.verdicts) == 7
    checks["has_recommendation"] = report.overall_recommendation in ("approve", "revise", "reject")

    # Graph thiếu CTA
    g_bad = DesignGraph(graph_id="g_bad", target=RenderTarget.REACT, root_id="root")
    g_bad.add_node(DesignNode(node_id="root", component_id="page.landing"))
    g_bad.add_node(DesignNode(node_id="hero", component_id="organism.hero", metadata={"feature_id": "hero"}))
    g_bad.link("root", "main", "hero")
    report_bad = rt.deliberate(CriticInput(graph=g_bad, catalog=catalog, brief_product_type="landing_page"))
    ux_verdict = next(v for v in report_bad.verdicts if v.critic_id == "C1")
    checks["ux_rejects_missing_cta"] = ux_verdict.status == CriticVerdictStatus.REJECT

    # Security: hardcoded secret
    g_sec = DesignGraph(graph_id="g_sec", target=RenderTarget.REACT, root_id="root")
    g_sec.add_node(DesignNode(node_id="root", component_id="page.landing"))
    g_sec.add_node(DesignNode(
        node_id="api", component_id="molecule.api_client",
        props={"apiKey": "sk-1234567890"},
    ))
    g_sec.link("root", "main", "api")
    report_sec = rt.deliberate(CriticInput(graph=g_sec, catalog=catalog, brief_product_type="saas_app"))
    sec_verdict = next(v for v in report_sec.verdicts if v.critic_id == "C5")
    checks["security_catches_secret"] = sec_verdict.status == CriticVerdictStatus.REJECT

    return checks


__all__ = [
    "UI_CRITICS_VERSION",
    "CriticVerdictStatus", "UIFinding", "UICriticVerdict",
    "CriticInput", "UICritic",
    "UXHeuristicCritic", "PerformanceCritic", "AccessibilityCritic",
    "SEOCritic", "SecurityCritic", "CodeSmellCritic", "BrandConsistencyCritic",
    "DEFAULT_UI_CRITICS", "RoundTableV6Report", "RoundTableV6",
    "ui_critics_sanity_check",
]
