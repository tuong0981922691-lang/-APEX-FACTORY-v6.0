"""
APEX FACTORY v6.0 - Deliberation Layer (v6)
File: quality_gate.py

Mục đích: QUALITY GATE - cửa ải cuối của deliberation layer.
    Tổng hợp 3 nguồn tín hiệu:
      1. Radar 4D Report (radar_4d.py)
      2. Round Table V6 Report (ui_critics.py)
      3. AbstainPolicy legacy (kế thừa nguyên vẹn)
    + optional B3 CritiqueReport (pre-synthesis)

    Quyết định cuối: APPROVED / REVISION_REQUIRED / REJECTED / ABSTAIN

Triết lý NT5 + NT6:
    - KHÔNG bịa composite = "xác suất thành công"; đó là metric nội bộ.
    - C2 có thể override mọi REJECT nếu ký Capability Token hợp lệ.
    - ABSTAIN không phải lỗi - là tín hiệu "brief không đủ để quyết định".
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from apex_core.deliberation_v6.radar_4d import (
    Radar4DReport,
    RadarAxis,
)
from apex_core.deliberation_v6.ui_critics import (
    RoundTableV6Report,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)

# Kế thừa AbstainPolicy từ legacy v5.0
from apex_core.legacy.deliberation.abstain_policy import (
    AbstainPolicyEngine,
    AbstainReason,
)

# Capability Token legacy cho c2_override
from apex_core.legacy.foundation.capability_token import (
    CapabilityGate,
    CapabilityToken,
)

# ============================================================
# 0. VERSION
# ============================================================

QUALITY_GATE_VERSION = "6.0.0"


# ============================================================
# 1. DECISION STATUS + FIX PROPOSAL
# ============================================================

class QualityDecisionStatus(str, Enum):
    APPROVED = "approved"           # Đủ chuẩn → phát tiếp cho emitter
    REVISION_REQUIRED = "revision"  # Còn fix được → B6 re-run với suggestions
    REJECTED = "rejected"           # Không cứu được → quay lại B4 sinh variant mới
    ABSTAIN = "abstain"             # Không đủ thông tin để quyết định
    C2_VETO = "c2_veto"             # C2 chủ động veto
    C2_OVERRIDE_APPROVED = "c2_override_approved"   # Bình thường reject nhưng C2 override


class FixKind(str, Enum):
    ADD_COMPONENT = "add_component"
    REMOVE_COMPONENT = "remove_component"
    CHANGE_PROP = "change_prop"
    UPGRADE_TOKEN = "upgrade_token"
    ADD_ARIA = "add_aria"
    SPLIT_NODE = "split_node"
    LAZY_LOAD = "lazy_load"
    OTHER = "other"


@dataclass(frozen=True)
class FixProposal:
    """Đề xuất fix cụ thể để B6 xử lý."""
    fix_id: str
    kind: FixKind
    title: str
    description: str
    target_node_ids: Tuple[str, ...] = ()
    priority: int = 5               # 1 = cao nhất
    source_critic_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self) | {"kind": self.kind.value}


# ============================================================
# 2. QUALITY GATE THRESHOLDS
# ============================================================

@dataclass(frozen=True)
class QualityGateThresholds:
    """Ngưỡng quyết định. Có thể override cho từng domain."""
    # Radar 4D
    min_composite_radar: float = 0.55
    min_axis_speed: float = 0.40
    min_axis_footprint: float = 0.40
    min_axis_stability: float = 0.50
    min_axis_cleanliness: float = 0.40

    # Round Table
    max_critic_rejects: int = 2
    max_avg_concern: float = 0.55

    # Composite gate
    min_composite_quality: float = 0.55
    approve_threshold: float = 0.75
    reject_threshold: float = 0.40

    # Weights for composite
    radar_weight: float = 0.55
    round_table_weight: float = 0.35
    critique_weight: float = 0.10

    def __post_init__(self):
        total = self.radar_weight + self.round_table_weight + self.critique_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0: got {total}")


DEFAULT_THRESHOLDS = QualityGateThresholds()


# ============================================================
# 3. QUALITY DECISION
# ============================================================

@dataclass
class QualityDecision:
    decision_id: str
    graph_id: str
    status: QualityDecisionStatus
    composite_quality: float                # 0..1
    radar_composite: float
    round_table_concern: float
    critique_health_score: float            # 0..1 (từ B3)

    # Breakdown chi tiết
    radar_report_dict: Dict[str, Any]
    round_table_dict: Dict[str, Any]
    abstain_info: Optional[Dict[str, Any]]

    # Actionable
    fix_proposals: List[FixProposal] = field(default_factory=list)

    # Meta
    c2_override_token_id: Optional[str] = None
    rejection_reasons: Tuple[str, ...] = ()
    approval_notes: Tuple[str, ...] = ()
    message: str = ""

    def is_approved(self) -> bool:
        return self.status in (
            QualityDecisionStatus.APPROVED,
            QualityDecisionStatus.C2_OVERRIDE_APPROVED,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "composite_quality": round(self.composite_quality, 4),
            "radar_composite": round(self.radar_composite, 4),
            "round_table_concern": round(self.round_table_concern, 4),
            "critique_health_score": round(self.critique_health_score, 4),
            "radar_report": self.radar_report_dict,
            "round_table": self.round_table_dict,
            "abstain_info": self.abstain_info,
            "fix_proposals": [f.to_dict() for f in self.fix_proposals],
            "c2_override_token_id": self.c2_override_token_id,
            "rejection_reasons": list(self.rejection_reasons),
            "approval_notes": list(self.approval_notes),
            "message": self.message,
        }


# ============================================================
# 4. FIX PROPOSAL GENERATOR
# ============================================================

class FixProposalBuilder:
    """Từ findings của Round Table + Radar → sinh FixProposal."""

    @staticmethod
    def build_from_round_table(rt_report: RoundTableV6Report) -> List[FixProposal]:
        proposals: List[FixProposal] = []
        counter = 0
        # Map finding.title/suggestion → FixKind
        for verdict in rt_report.verdicts:
            for finding in verdict.findings:
                kind = FixProposalBuilder._infer_kind(finding.title)
                priority = {
                    "error": 2, "warning": 5, "info": 8,
                }.get(finding.severity, 5)
                counter += 1
                proposals.append(FixProposal(
                    fix_id=f"fix_rt_{counter:04d}",
                    kind=kind,
                    title=finding.title,
                    description=f"{finding.message} | {finding.suggestion}",
                    target_node_ids=finding.affected_node_ids,
                    priority=priority,
                    source_critic_id=verdict.critic_id,
                ))
        return proposals

    @staticmethod
    def build_from_radar(radar: Radar4DReport) -> List[FixProposal]:
        proposals: List[FixProposal] = []
        counter = 0
        for axis in radar.axes:
            for warn in axis.warnings:
                counter += 1
                kind = FixKind.OTHER
                if axis.axis == RadarAxis.FOOTPRINT:
                    kind = FixKind.LAZY_LOAD
                elif axis.axis == RadarAxis.SPEED and "animation" in warn.lower():
                    kind = FixKind.CHANGE_PROP
                elif axis.axis == RadarAxis.STABILITY and "missing" in warn.lower():
                    kind = FixKind.CHANGE_PROP
                elif axis.axis == RadarAxis.CLEANLINESS:
                    kind = FixKind.SPLIT_NODE
                proposals.append(FixProposal(
                    fix_id=f"fix_radar_{counter:04d}",
                    kind=kind,
                    title=f"{axis.axis.value} - {axis.grade}",
                    description=warn,
                    priority=4 if axis.grade in ("D", "F") else 6,
                    source_critic_id=f"radar_{axis.axis.value}",
                ))
        return proposals

    @staticmethod
    def _infer_kind(title: str) -> FixKind:
        t = title.lower()
        if "cta" in t or "missing" in t and "heading" not in t:
            return FixKind.ADD_COMPONENT
        if "aria" in t or "label" in t or "keyboard" in t:
            return FixKind.ADD_ARIA
        if "god node" in t or "nesting" in t:
            return FixKind.SPLIT_NODE
        if "bundle" in t or "heavy" in t:
            return FixKind.LAZY_LOAD
        if "drift" in t or "token" in t or "brand" in t:
            return FixKind.UPGRADE_TOKEN
        if "orphan" in t:
            return FixKind.REMOVE_COMPONENT
        return FixKind.OTHER


# ============================================================
# 5. QUALITY GATE (main)
# ============================================================

class QualityGate:
    def __init__(
        self,
        thresholds: Optional[QualityGateThresholds] = None,
        abstain_engine: Optional[AbstainPolicyEngine] = None,
        capability_gate: Optional[CapabilityGate] = None,
    ):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        self.abstain_engine = abstain_engine
        self.capability_gate = capability_gate
        self._decisions: Dict[str, QualityDecision] = {}
        self._counter = 0

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    @enforce_principle_v6(PrincipleV6.NT6_NO_RANDOM_CONCLUSION)
    def evaluate(
        self,
        *,
        graph_id: str,
        radar_report: Radar4DReport,
        round_table_report: RoundTableV6Report,
        critique_health_score: float = 1.0,
        vault_snapshot: Optional[Mapping[str, Any]] = None,
        kill_switch_active: bool = False,
        c2_signal: Optional[str] = None,
    ) -> QualityDecision:
        th = self.thresholds

        # --------- Composite Quality ---------
        radar_composite = radar_report.composite
        # Round table concern → quality (càng ít concern càng cao)
        rt_quality = max(0.0, 1.0 - round_table_report.avg_concern)

        composite = (
            th.radar_weight * radar_composite
            + th.round_table_weight * rt_quality
            + th.critique_weight * critique_health_score
        )
        composite = round(composite, 4)

        # --------- Hard gate checks ---------
        rejection_reasons: List[str] = []
        approval_notes: List[str] = []

        # Check axes từng trục
        for axis in radar_report.axes:
            min_allowed = {
                RadarAxis.SPEED: th.min_axis_speed,
                RadarAxis.FOOTPRINT: th.min_axis_footprint,
                RadarAxis.STABILITY: th.min_axis_stability,
                RadarAxis.CLEANLINESS: th.min_axis_cleanliness,
            }.get(axis.axis, 0.4)
            if axis.normalized_score < min_allowed:
                rejection_reasons.append(
                    f"{axis.axis.value} score {axis.normalized_score:.2f} "
                    f"< threshold {min_allowed}"
                )

        # Radar composite threshold
        if radar_composite < th.min_composite_radar:
            rejection_reasons.append(
                f"Radar composite {radar_composite:.2f} < {th.min_composite_radar}"
            )

        # Round Table rejects
        if round_table_report.reject_count > th.max_critic_rejects:
            rejection_reasons.append(
                f"Round Table rejects {round_table_report.reject_count} "
                f"> max {th.max_critic_rejects}"
            )
        if round_table_report.avg_concern > th.max_avg_concern:
            rejection_reasons.append(
                f"Round Table avg_concern {round_table_report.avg_concern:.2f} "
                f"> max {th.max_avg_concern}"
            )

        # --------- Abstain check (legacy engine) ---------
        abstain_info: Optional[Dict[str, Any]] = None
        if self.abstain_engine is not None:
            # Map Round Table V6 → schema legacy expects
            rt_legacy_shape = {
                "status": (
                    "ABSTAIN" if round_table_report.overall_recommendation == "reject"
                    else "OK"
                ),
                "decision_trace": {
                    "avg_concern": round_table_report.avg_concern,
                    "reject_count": round_table_report.reject_count,
                },
            }
            confidence_gate_shape = {
                "should_abstain": composite < th.min_composite_quality,
                "failures": rejection_reasons,
            }
            abstain_dec = self.abstain_engine.evaluate(
                round_table_result=rt_legacy_shape,
                confidence_gate_result=confidence_gate_shape,
                vault_snapshot=dict(vault_snapshot or {}),
                kill_switch_active=kill_switch_active,
                c2_signal=c2_signal,
            )
            abstain_info = {
                "should_abstain": abstain_dec.should_abstain,
                "primary_reason": abstain_dec.primary_reason,
                "severity": abstain_dec.severity,
                "can_override_by_c2": abstain_dec.can_override_by_c2,
                "recommended_action": abstain_dec.recommended_action,
            }
            # Critical abstain (kill switch, C2 veto) → terminate ngay
            if abstain_dec.severity == "critical":
                return self._build_decision(
                    graph_id=graph_id,
                    status=(
                        QualityDecisionStatus.C2_VETO
                        if abstain_dec.primary_reason == AbstainReason.C2_VETO
                        else QualityDecisionStatus.ABSTAIN
                    ),
                    composite=composite,
                    radar=radar_report,
                    rt=round_table_report,
                    critique_score=critique_health_score,
                    abstain_info=abstain_info,
                    rejection_reasons=(abstain_dec.primary_reason,),
                    fix_proposals=[],
                    message=f"CRITICAL abstain: {abstain_dec.primary_reason}",
                )

        # --------- Fix proposals ---------
        fixes = FixProposalBuilder.build_from_round_table(round_table_report)
        fixes += FixProposalBuilder.build_from_radar(radar_report)
        # Sort by priority
        fixes.sort(key=lambda f: f.priority)

        # --------- Final decision ---------
        hard_rejected = len(rejection_reasons) > 0 or composite < th.reject_threshold

        if hard_rejected:
            status = QualityDecisionStatus.REJECTED
            message = (
                f"REJECTED: composite={composite:.2f}, "
                f"{len(rejection_reasons)} hard-gate fails"
            )
        elif composite >= th.approve_threshold and round_table_report.reject_count == 0:
            status = QualityDecisionStatus.APPROVED
            approval_notes.append(
                f"composite={composite:.2f} >= approve_threshold={th.approve_threshold}"
            )
            message = f"APPROVED: composite {composite:.2f} (grade {radar_report.composite_grade})"
        elif composite >= th.min_composite_quality:
            status = QualityDecisionStatus.REVISION_REQUIRED
            message = (
                f"REVISION: composite {composite:.2f} trong khoảng "
                f"[{th.min_composite_quality}, {th.approve_threshold}) - "
                f"{len(fixes)} fix proposals"
            )
        else:
            # Giữa reject_threshold và min_composite → abstain nếu không có hard reason,
            # ngược lại cho revision
            if abstain_info and abstain_info["should_abstain"]:
                status = QualityDecisionStatus.ABSTAIN
                message = f"ABSTAIN: {abstain_info.get('primary_reason', 'low_composite')}"
            else:
                status = QualityDecisionStatus.REVISION_REQUIRED
                message = f"REVISION (borderline): composite {composite:.2f}"

        decision = self._build_decision(
            graph_id=graph_id,
            status=status,
            composite=composite,
            radar=radar_report,
            rt=round_table_report,
            critique_score=critique_health_score,
            abstain_info=abstain_info,
            rejection_reasons=tuple(rejection_reasons),
            approval_notes=tuple(approval_notes),
            fix_proposals=fixes,
            message=message,
        )
        self._decisions[decision.decision_id] = decision
        return decision

    def evaluate_variants(
        self,
        *,
        variant_radar_reports: Sequence[Radar4DReport],
        variant_round_tables: Sequence[RoundTableV6Report],
        critique_health_score: float = 1.0,
        vault_snapshot: Optional[Mapping[str, Any]] = None,
        kill_switch_active: bool = False,
        c2_signal: Optional[str] = None,
    ) -> Tuple[Optional[QualityDecision], List[QualityDecision]]:
        """
        Chạy gate trên N variant, trả về (best_approved_or_revision, all_decisions).
        Best = highest composite_quality trong nhóm approved/revision.
        """
        if len(variant_radar_reports) != len(variant_round_tables):
            raise ValueError(
                "Số lượng radar reports và round-table reports phải bằng nhau"
            )
        all_decisions: List[QualityDecision] = []
        for radar, rt in zip(variant_radar_reports, variant_round_tables):
            decision = self.evaluate(
                graph_id=radar.graph_id,
                radar_report=radar,
                round_table_report=rt,
                critique_health_score=critique_health_score,
                vault_snapshot=vault_snapshot,
                kill_switch_active=kill_switch_active,
                c2_signal=c2_signal,
            )
            all_decisions.append(decision)

        # Pick best: ưu tiên APPROVED, sau đó REVISION
        eligible = [
            d for d in all_decisions
            if d.status in (
                QualityDecisionStatus.APPROVED,
                QualityDecisionStatus.REVISION_REQUIRED,
            )
        ]
        if not eligible:
            return None, all_decisions
        best = max(eligible, key=lambda d: d.composite_quality)
        return best, all_decisions

    # ------------- C2 Override (NT5) -------------

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def c2_override_approve(
        self,
        decision_id: str,
        token: CapabilityToken,
    ) -> Dict[str, Any]:
        """
        C2 ép approve 1 decision đã REJECTED/REVISION bằng Capability Token.
        KHÔNG override được C2_VETO hoặc kill-switch-driven ABSTAIN.
        """
        decision = self._decisions.get(decision_id)
        if decision is None:
            return {"success": False, "error": "decision_not_found"}
        if decision.status in (
            QualityDecisionStatus.C2_VETO,
            QualityDecisionStatus.APPROVED,
            QualityDecisionStatus.C2_OVERRIDE_APPROVED,
        ):
            return {
                "success": False,
                "error": f"cannot_override_{decision.status.value}",
            }
        # Abstain với severity=critical cũng không override được
        if decision.abstain_info and decision.abstain_info.get("severity") == "critical":
            return {"success": False, "error": "critical_abstain_cannot_override"}

        if self.capability_gate is None:
            return {"success": False, "error": "capability_gate_not_configured"}

        try:
            self.capability_gate.authorize(
                token=token,
                required_scope="override_decision",
                required_resource=f"quality_decision:{decision_id}",
            )
        except Exception as e:
            return {"success": False, "error": f"gate_rejected: {e}"}

        decision.status = QualityDecisionStatus.C2_OVERRIDE_APPROVED
        decision.c2_override_token_id = token.token_id
        decision.approval_notes = decision.approval_notes + (
            f"C2 override via token {token.token_id}",
        )
        decision.message = (
            f"C2 OVERRIDE APPROVED (original: {decision.rejection_reasons[:2]})"
        )
        return {
            "success": True,
            "decision_id": decision_id,
            "new_status": decision.status.value,
        }

    # ------------- Helpers -------------

    def _next_id(self) -> str:
        self._counter += 1
        return f"qd_{self._counter:06d}"

    def _build_decision(
        self,
        *,
        graph_id: str,
        status: QualityDecisionStatus,
        composite: float,
        radar: Radar4DReport,
        rt: RoundTableV6Report,
        critique_score: float,
        abstain_info: Optional[Dict[str, Any]],
        fix_proposals: List[FixProposal],
        rejection_reasons: Tuple[str, ...] = (),
        approval_notes: Tuple[str, ...] = (),
        message: str = "",
    ) -> QualityDecision:
        return QualityDecision(
            decision_id=self._next_id(),
            graph_id=graph_id,
            status=status,
            composite_quality=composite,
            radar_composite=radar.composite,
            round_table_concern=rt.avg_concern,
            critique_health_score=critique_score,
            radar_report_dict=radar.to_dict(),
            round_table_dict=rt.to_dict(),
            abstain_info=abstain_info,
            fix_proposals=fix_proposals,
            rejection_reasons=rejection_reasons,
            approval_notes=approval_notes,
            message=message,
        )

    def get_decision(self, decision_id: str) -> Optional[QualityDecision]:
        return self._decisions.get(decision_id)

    def summary(self) -> Dict[str, Any]:
        status_counts: Dict[str, int] = {}
        for d in self._decisions.values():
            status_counts[d.status.value] = status_counts.get(d.status.value, 0) + 1
        return {
            "total_decisions": len(self._decisions),
            "status_counts": status_counts,
        }


# ============================================================
# 6. SANITY CHECK
# ============================================================

def quality_gate_sanity_check() -> Dict[str, bool]:
    from apex_core.deliberation_v6.radar_4d import Radar4DScorer
    from apex_core.deliberation_v6.ui_critics import (
        CriticInput,
        RoundTableV6,
    )
    from apex_core.foundation.ontology_ui import ComponentCatalog
    from apex_core.foundation.ui_ir import DesignGraph, DesignNode, RenderTarget

    checks: Dict[str, bool] = {}

    # Build 1 graph khỏe
    g_good = DesignGraph(graph_id="g_good", target=RenderTarget.REACT, root_id="root")
    g_good.add_node(DesignNode(node_id="root", component_id="page.landing"))
    for i, (cid, fid) in enumerate([
        ("organism.navbar", "navbar"),
        ("organism.hero", "hero"),
        ("atom.button.primary", "cta"),
        ("organism.footer", "footer"),
    ]):
        nid = f"n{i}"
        g_good.add_node(DesignNode(node_id=nid, component_id=cid, metadata={"feature_id": fid}))
        g_good.link("root", "main", nid)

    catalog = ComponentCatalog()
    radar = Radar4DScorer().evaluate(g_good, catalog, {"_product_type": "landing_page"})
    rt = RoundTableV6().deliberate(CriticInput(
        graph=g_good, catalog=catalog, radar_report=radar,
        brief_product_type="landing_page",
    ))

    gate = QualityGate()
    decision = gate.evaluate(
        graph_id=g_good.graph_id,
        radar_report=radar,
        round_table_report=rt,
        critique_health_score=0.95,
    )
    checks["decision_exists"] = decision is not None
    checks["decision_valid_status"] = decision.status in QualityDecisionStatus
    checks["has_composite"] = 0.0 <= decision.composite_quality <= 1.0

    # Build 1 graph kém (placeholder nặng, nhiều feature missing)
    g_bad = DesignGraph(graph_id="g_bad", target=RenderTarget.REACT, root_id="root")
    g_bad.add_node(DesignNode(node_id="root", component_id="placeholder.page.container"))
    for i in range(8):
        nid = f"ph{i}"
        g_bad.add_node(DesignNode(
            node_id=nid, component_id="placeholder.organism.section",
            metadata={"needs_llm_fill": True},
        ))
        g_bad.link("root", "main", nid)

    radar_bad = Radar4DScorer().evaluate(g_bad, catalog, {"_product_type": "landing_page"})
    rt_bad = RoundTableV6().deliberate(CriticInput(
        graph=g_bad, catalog=catalog, radar_report=radar_bad,
        brief_product_type="landing_page",
    ))
    decision_bad = gate.evaluate(
        graph_id=g_bad.graph_id,
        radar_report=radar_bad,
        round_table_report=rt_bad,
        critique_health_score=0.5,
    )
    checks["bad_rejected_or_abstain"] = decision_bad.status in (
        QualityDecisionStatus.REJECTED,
        QualityDecisionStatus.REVISION_REQUIRED,
        QualityDecisionStatus.ABSTAIN,
    )
    checks["bad_has_fix_proposals"] = len(decision_bad.fix_proposals) > 0

    # Evaluate variants
    best, all_decs = gate.evaluate_variants(
        variant_radar_reports=[radar, radar_bad],
        variant_round_tables=[rt, rt_bad],
        critique_health_score=0.9,
    )
    checks["three_decisions_total"] = len(all_decs) == 2
    checks["best_picked"] = best is None or best.graph_id in {"g_good", "g_bad"}

    # C2 override without gate configured
    override_result = gate.c2_override_approve(
        decision_id=decision_bad.decision_id,
        token=None,   # type: ignore  (fake)
    )
    # Will fail because capability_gate is None, but function must not crash
    checks["override_fails_gracefully"] = not override_result["success"]

    return checks


__all__ = [
    "QUALITY_GATE_VERSION",
    "QualityDecisionStatus", "FixKind", "FixProposal",
    "QualityGateThresholds", "DEFAULT_THRESHOLDS",
    "QualityDecision",
    "FixProposalBuilder",
    "QualityGate",
    "quality_gate_sanity_check",
]
