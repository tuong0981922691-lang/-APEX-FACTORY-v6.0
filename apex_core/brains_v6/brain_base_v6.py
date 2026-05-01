"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: brain_base_v6.py

Mục đích: Lớp nền cho 7 bộ não mới của Factory. KẾ THỪA NGUYÊN VẸN
          BaseBrain/BrainResult/lifecycle hooks từ legacy v5.0 để KHÔNG
          phải viết lại hạ tầng đo thời gian, audit, error isolation.

Chỉ BỔ SUNG:
  - FactoryBrainContext: context mở rộng chứa catalog/registry/graph
  - FactoryBrainResult: result có thêm graph_diff + radar_embed
  - BrainStage enum: đánh dấu vị trí brain trong pipeline
  - Helpers: require_catalog, require_registry, build_snapshot_from_result

Nguyên tắc: TUYỆT ĐỐI KHÔNG sửa code legacy. Chỉ wrap + extend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from apex_core.foundation.domain_types import DomainRegistry, DomainType
from apex_core.foundation.ontology_media import SceneGraph
from apex_core.foundation.ontology_ui import ComponentCatalog, TokenRegistry
from apex_core.foundation.project_snapshot import ProjectLineage, ProjectSnapshot
from apex_core.foundation.ui_ir import DesignGraph

# Re-export legacy base - code Phase 1+ chỉ import từ file này
from apex_core.legacy.brains.brain_base import (
    BaseBrain,
    BrainContext,
    BrainLifecycleHooks,
    BrainResult,
    NoOpHooks,
    time_it,
)
from apex_core.legacy.foundation.contracts import BrainState

if TYPE_CHECKING:
    # Tránh circular import: BriefSpec nằm ở b1_intent_ingestor
    from apex_core.brains_v6.b1_intent_ingestor import BriefSpec


# ============================================================
# 0. VERSION
# ============================================================

BRAIN_BASE_V6_VERSION = "6.0.0"


# ============================================================
# 1. BRAIN STAGE (vị trí trong pipeline)
# ============================================================

class BrainStage(str, Enum):
    """Vị trí của brain trong pipeline. Giúp Orchestrator order đúng."""
    INGEST = "ingest"               # B1
    SCOUT = "scout"                 # B2
    CRITIQUE_PRE = "critique_pre"   # B3
    SYNTHESIZE = "synthesize"       # B4
    VAULT = "vault"                 # B5 (tái dùng legacy)
    COMMAND = "command"             # B6
    FORGE = "forge"                 # B7
    POST_PROCESS = "post_process"   # optional


STAGE_ORDER: tuple = (
    BrainStage.INGEST,
    BrainStage.SCOUT,
    BrainStage.CRITIQUE_PRE,
    BrainStage.SYNTHESIZE,
    BrainStage.VAULT,
    BrainStage.COMMAND,
    BrainStage.FORGE,
    BrainStage.POST_PROCESS,
)


# ============================================================
# 2. FACTORY BRAIN CONTEXT (mở rộng BrainContext legacy)
# ============================================================

@dataclass
class FactoryBrainContext(BrainContext):
    """
    Context mở rộng cho factory pipeline.
    Kế thừa từ legacy BrainContext để BaseBrain.run() vẫn chạy.

    Legacy fields giữ nguyên với ý nghĩa mới:
        - draws       : không dùng (để empty list)
        - current_idx : không dùng (để 0)
        - current_date: YYYY-MM-DD của run hiện tại
        - config      : config run-time
        - shared_memory: chia sẻ output giữa các brain (cùng pipeline)
    """
    # --- Factory-specific fields (đều có default để dataclass inheritance OK) ---
    project_id: str = ""
    run_mode: str = "production"                  # "production" | "shadow" | "simulation"

    # Brief (sẽ được set sau khi B1 chạy xong)
    brief_spec: Optional["BriefSpec"] = None

    # Domain routing
    target_domain: Optional[DomainType] = None
    domain_registry: Optional[DomainRegistry] = None

    # Ontology refs (FK vào các registry của Factory)
    component_catalog: Optional[ComponentCatalog] = None
    token_registry: Optional[TokenRegistry] = None

    # Graph đang thi công (mutable giữa các brain)
    active_design_graph: Optional[DesignGraph] = None
    active_scene_graph: Optional[SceneGraph] = None
    variant_graphs: List[DesignGraph] = field(default_factory=list)

    # Lineage (chain of ProjectSnapshot)
    snapshot_lineage: Optional[ProjectLineage] = None

    # LLM Broker (Borrowing Protocol) - None nếu offline mode
    llm_broker: Any = None

    # Hooks đã thực hiện (để audit)
    executed_stages: List[BrainStage] = field(default_factory=list)

    # --------- Helpers ---------
    def require_catalog(self) -> ComponentCatalog:
        if self.component_catalog is None:
            raise RuntimeError("FactoryBrainContext: component_catalog chưa được set")
        return self.component_catalog

    def require_registry(self) -> TokenRegistry:
        if self.token_registry is None:
            raise RuntimeError("FactoryBrainContext: token_registry chưa được set")
        return self.token_registry

    def require_brief(self) -> "BriefSpec":
        if self.brief_spec is None:
            raise RuntimeError(
                "FactoryBrainContext: brief_spec chưa có - B1 phải chạy trước"
            )
        return self.brief_spec

    def has_llm(self) -> bool:
        return self.llm_broker is not None

    def mark_stage_done(self, stage: BrainStage) -> None:
        if stage not in self.executed_stages:
            self.executed_stages.append(stage)


# ============================================================
# 3. FACTORY BRAIN RESULT (bổ sung field cho factory)
# ============================================================

@dataclass
class FactoryBrainResult(BrainResult):
    """
    Result mở rộng. Kế thừa BrainResult để BaseBrain.run() vẫn dùng được.
    Bổ sung: graph_diff_summary, radar_preview, emitted_snapshot_id.
    """
    stage: Optional[str] = None                   # BrainStage.value
    emitted_snapshot_id: Optional[str] = None
    graph_diff_summary: Optional[Dict[str, Any]] = None
    radar_preview: Optional[Dict[str, Any]] = None
    llm_calls: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brain_id": self.brain_id,
            "success": self.success,
            "outputs": dict(self.outputs),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metrics": dict(self.metrics),
            "elapsed_ms": self.elapsed_ms,
            "stage": self.stage,
            "emitted_snapshot_id": self.emitted_snapshot_id,
            "graph_diff_summary": self.graph_diff_summary,
            "radar_preview": self.radar_preview,
            "llm_calls": self.llm_calls,
        }


# ============================================================
# 4. BASE CLASS CHO BRAIN V6 (kế thừa BaseBrain legacy + add stage)
# ============================================================

class FactoryBrain(BaseBrain):
    """
    Base class cho mọi brain v6. Sub-class phải:
      - Set BRAIN_STAGE
      - Implement execute(context) -> FactoryBrainResult
      - Khai báo REQUIRED_CONTEXT để validate_context chạy tự động
    """
    BRAIN_ID: str = "B?"
    BRAIN_NAME: str = "FactoryBrain"
    BRAIN_STAGE: BrainStage = BrainStage.POST_PROCESS
    REQUIRED_INPUTS: tuple = ()

    # Factory-specific required context attributes (khác với REQUIRED_INPUTS là key của shared_memory)
    REQUIRED_CONTEXT_ATTRS: tuple = ()
    # Ví dụ: ("component_catalog", "token_registry") → sẽ check thuộc tính context phải non-None

    def validate_inputs(self, context: BrainContext) -> List[str]:
        """Kết hợp check legacy (shared_memory) + factory context attrs."""
        missing = super().validate_inputs(context)
        if isinstance(context, FactoryBrainContext):
            for attr_name in self.REQUIRED_CONTEXT_ATTRS:
                val = getattr(context, attr_name, None)
                if val is None:
                    missing.append(f"context.{attr_name} is None")
        return missing

    def _wrap_result(self, result: BrainResult) -> FactoryBrainResult:
        """Convert plain BrainResult → FactoryBrainResult nếu subclass lỡ return nhầm."""
        if isinstance(result, FactoryBrainResult):
            if result.stage is None:
                result.stage = self.BRAIN_STAGE.value
            return result
        return FactoryBrainResult(
            brain_id=result.brain_id or self.BRAIN_ID,
            success=result.success,
            outputs=dict(result.outputs),
            warnings=list(result.warnings),
            errors=list(result.errors),
            metrics=dict(result.metrics),
            elapsed_ms=result.elapsed_ms,
            stage=self.BRAIN_STAGE.value,
        )

    def run(self, context: BrainContext) -> FactoryBrainResult:
        """Override để đảm bảo luôn trả FactoryBrainResult + mark stage."""
        base_result = super().run(context)
        wrapped = self._wrap_result(base_result)
        if isinstance(context, FactoryBrainContext) and wrapped.success:
            context.mark_stage_done(self.BRAIN_STAGE)
        return wrapped


# ============================================================
# 5. HELPERS CHUNG CHO BRAINS V6
# ============================================================

def snapshot_from_factory_result(
    context: FactoryBrainContext,
    result: FactoryBrainResult,
    *,
    snapshot_id: str,
    version_label: str,
    stage_tag: str = "draft",
) -> Optional[ProjectSnapshot]:
    """
    Tạo ProjectSnapshot từ state hiện tại của context + result.
    Chỉ thành công nếu có design_graph hoặc scene_graph.
    """
    from apex_core.foundation.project_snapshot import (
        ProjectStage,
        build_snapshot_from_design_graph,
        build_snapshot_from_scene_graph,
    )

    brief_hash = (
        context.brief_spec.content_hash if context.brief_spec else "unknown"
    )
    brief_summary = (
        (context.brief_spec.raw_text[:500] if context.brief_spec else "")
    )
    domain_value = (
        context.target_domain.value if context.target_domain else "web"
    )
    parent_id: Optional[str] = None
    if context.snapshot_lineage and context.snapshot_lineage.head_snapshot_id:
        parent_id = context.snapshot_lineage.head_snapshot_id

    try:
        stage_enum = ProjectStage(stage_tag)
    except ValueError:
        stage_enum = ProjectStage.DRAFT

    if context.active_design_graph is not None:
        return build_snapshot_from_design_graph(
            project_id=context.project_id or "default_project",
            snapshot_id=snapshot_id,
            version_label=version_label,
            domain=domain_value,
            graph=context.active_design_graph,
            brief_hash=brief_hash,
            brief_summary=brief_summary,
            parent_snapshot_id=parent_id,
            token_registry_fingerprint=(
                context.token_registry.fingerprint() if context.token_registry else ""
            ),
            component_catalog_fingerprint=(
                context.component_catalog.fingerprint() if context.component_catalog else ""
            ),
            stage=stage_enum,
            created_by=result.brain_id,
            tags=("factory_v6",),
        )

    if context.active_scene_graph is not None:
        return build_snapshot_from_scene_graph(
            project_id=context.project_id or "default_project",
            snapshot_id=snapshot_id,
            version_label=version_label,
            domain=domain_value,
            scene=context.active_scene_graph,
            brief_hash=brief_hash,
            brief_summary=brief_summary,
            parent_snapshot_id=parent_id,
            stage=stage_enum,
            created_by=result.brain_id,
            tags=("factory_v6", "video"),
        )

    return None


# ============================================================
# 6. SANITY CHECK
# ============================================================

def brain_base_v6_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    # FactoryBrainContext khởi tạo OK với minimal args
    try:
        ctx = FactoryBrainContext(
            run_id="r1",
            current_date="2025-01-01",
            draws=[],
            current_idx=0,
        )
        checks["context_minimal_init"] = isinstance(ctx, BrainContext)
    except Exception:
        checks["context_minimal_init"] = False

    # require_brief raise khi chưa set
    try:
        ctx.require_brief()
        checks["require_brief_raises"] = False
    except RuntimeError:
        checks["require_brief_raises"] = True

    # mark_stage_done accumulate
    ctx.mark_stage_done(BrainStage.INGEST)
    ctx.mark_stage_done(BrainStage.INGEST)   # dedup
    ctx.mark_stage_done(BrainStage.SCOUT)
    checks["stage_dedup"] = len(ctx.executed_stages) == 2

    # FactoryBrainResult to_dict OK
    try:
        r = FactoryBrainResult(
            brain_id="B_TEST",
            success=True,
            outputs={"x": 1},
            stage=BrainStage.INGEST.value,
        )
        checks["result_to_dict"] = r.to_dict()["stage"] == "ingest"
    except Exception:
        checks["result_to_dict"] = False

    # Stage order
    checks["stage_order_len"] = len(STAGE_ORDER) == 8
    checks["stage_order_ingest_first"] = STAGE_ORDER[0] == BrainStage.INGEST

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "BRAIN_BASE_V6_VERSION",
    # Re-exports from legacy (tiện import 1 nơi)
    "BaseBrain",
    "BrainContext",
    "BrainResult",
    "BrainLifecycleHooks",
    "NoOpHooks",
    "BrainState",
    "time_it",
    # v6 new
    "BrainStage",
    "STAGE_ORDER",
    "FactoryBrainContext",
    "FactoryBrainResult",
    "FactoryBrain",
    # Helpers
    "snapshot_from_factory_result",
    "brain_base_v6_sanity_check",
]
