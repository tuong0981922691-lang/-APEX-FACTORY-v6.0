"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: b6_commander.py

Vai trò B6: THE COMMANDER / ASSEMBLER ⭐
    Nhạc trưởng của Factory. Orchestrate B1→B2→B3→B4 theo thứ tự,
    xử lý placeholder bằng Borrowing Protocol, emit artifact cuối.

Borrowing Protocol ("Giao thức Mượn Tổ"):
    Khi có placeholder cần fill, B6 mượn LLM ngoài với 3 tầng bảo vệ:
      1. PROMPT GUARD   : prompt đã khung hóa, không cho LLM đọc brief raw
      2. SCHEMA GUARD   : bắt output JSON đúng schema, retry nếu lệch
      3. POST VALIDATOR : output phải pass rule engine (NT11, NT12, containment)

    KHÔNG bao giờ tin LLM mù quáng. LLM = công nhân thời vụ.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from apex_core.brains_v6.b1_intent_ingestor import B1IntentIngestor
from apex_core.brains_v6.b2_component_scout import B2ComponentScout
from apex_core.brains_v6.b3_design_critic import B3DesignCritic
from apex_core.brains_v6.b4_composition_synthesizer import B4CompositionSynthesizer
from apex_core.brains_v6.brain_base_v6 import (
    BrainStage,
    FactoryBrain,
    FactoryBrainContext,
    FactoryBrainResult,
    snapshot_from_factory_result,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.project_snapshot import ProjectStage

# ============================================================
# 0. VERSION
# ============================================================

B6_VERSION = "6.0.0"


# ============================================================
# 1. SCHEMA GUARD (validator tối thiểu, không phụ thuộc jsonschema)
# ============================================================

class SchemaGuardError(Exception):
    pass


class SchemaGuard:
    """
    Validator JSON Schema subset. Đủ dùng cho Borrowing Protocol.
    Phase 5 sẽ thay bằng jsonschema library đầy đủ.
    """

    @staticmethod
    def validate(payload: Any, schema: Dict[str, Any], path: str = "$") -> None:
        expected = schema.get("type")

        if expected == "object":
            if not isinstance(payload, dict):
                raise SchemaGuardError(f"{path}: expected object, got {type(payload).__name__}")
            required = schema.get("required", [])
            for k in required:
                if k not in payload:
                    raise SchemaGuardError(f"{path}: missing required key '{k}'")
            props = schema.get("properties", {})
            for k, v in payload.items():
                if schema.get("additionalProperties") is False and k not in props:
                    raise SchemaGuardError(f"{path}: unexpected key '{k}'")
                if k in props:
                    SchemaGuard.validate(v, props[k], f"{path}.{k}")

        elif expected == "array":
            if not isinstance(payload, list):
                raise SchemaGuardError(f"{path}: expected array, got {type(payload).__name__}")
            max_items = schema.get("maxItems")
            if max_items is not None and len(payload) > max_items:
                raise SchemaGuardError(f"{path}: array length {len(payload)} > maxItems {max_items}")
            item_schema = schema.get("items")
            if item_schema:
                for i, item in enumerate(payload):
                    SchemaGuard.validate(item, item_schema, f"{path}[{i}]")

        elif expected == "string":
            if not isinstance(payload, str):
                raise SchemaGuardError(f"{path}: expected string, got {type(payload).__name__}")
            max_len = schema.get("maxLength")
            if max_len is not None and len(payload) > max_len:
                raise SchemaGuardError(f"{path}: string length {len(payload)} > maxLength {max_len}")

        elif expected == "number":
            if not isinstance(payload, (int, float)) or isinstance(payload, bool):
                raise SchemaGuardError(f"{path}: expected number")

        elif expected == "integer":
            if not isinstance(payload, int) or isinstance(payload, bool):
                raise SchemaGuardError(f"{path}: expected integer")

        elif expected == "boolean":
            if not isinstance(payload, bool):
                raise SchemaGuardError(f"{path}: expected boolean")


# ============================================================
# 2. BORROWING PROTOCOL
# ============================================================

@dataclass(frozen=True)
class BorrowRequest:
    request_id: str
    purpose: str                            # "fill_placeholder_navbar" | ...
    prompt: str
    schema: Dict[str, Any]
    temperature: float = 0.2
    max_retries: int = 2


@dataclass
class BorrowResult:
    request_id: str
    success: bool
    output: Optional[Dict[str, Any]]
    attempts: int
    errors: List[str] = field(default_factory=list)
    llm_calls: int = 0


# Schema chuẩn cho 1 component fill request
PLACEHOLDER_FILL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["component_id", "props", "rationale"],
    "additionalProperties": False,
    "properties": {
        "component_id": {"type": "string", "maxLength": 120},
        "props":        {"type": "object"},
        "rationale":    {"type": "string", "maxLength": 500},
    },
}


class BorrowingProtocol:
    """
    Bóc lột LLM có trói buộc. KHÔNG tin output mù quáng.
    """

    def __init__(self, llm_broker: Any, schema_guard: Optional[SchemaGuard] = None):
        self.llm_broker = llm_broker
        self.guard = schema_guard or SchemaGuard()

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def borrow(self, request: BorrowRequest) -> BorrowResult:
        if self.llm_broker is None:
            return BorrowResult(
                request_id=request.request_id,
                success=False,
                output=None,
                attempts=0,
                errors=["llm_broker is None - offline mode"],
            )

        errors: List[str] = []
        for attempt in range(1, request.max_retries + 2):
            try:
                # Broker interface convention: call_with_schema(prompt, schema, **kw)
                if hasattr(self.llm_broker, "call_with_schema"):
                    raw_output = self.llm_broker.call_with_schema(
                        prompt=request.prompt,
                        schema=request.schema,
                        temperature=request.temperature,
                    )
                elif hasattr(self.llm_broker, "call"):
                    raw_output = self.llm_broker.call(
                        prompt=request.prompt,
                        temperature=request.temperature,
                    )
                    if isinstance(raw_output, str):
                        raw_output = json.loads(raw_output)
                else:
                    return BorrowResult(
                        request_id=request.request_id,
                        success=False,
                        output=None,
                        attempts=attempt,
                        errors=["llm_broker interface not recognized"],
                        llm_calls=attempt,
                    )

                self.guard.validate(raw_output, request.schema)
                return BorrowResult(
                    request_id=request.request_id,
                    success=True,
                    output=raw_output,
                    attempts=attempt,
                    llm_calls=attempt,
                )

            except SchemaGuardError as e:
                errors.append(f"attempt {attempt}: schema fail - {e}")
            except json.JSONDecodeError as e:
                errors.append(f"attempt {attempt}: invalid JSON - {e}")
            except Exception as e:
                errors.append(f"attempt {attempt}: {type(e).__name__} - {e}")

        return BorrowResult(
            request_id=request.request_id,
            success=False,
            output=None,
            attempts=request.max_retries + 1,
            errors=errors,
            llm_calls=request.max_retries + 1,
        )


# ============================================================
# 3. COMMANDER CONFIG
# ============================================================

@dataclass
class CommanderConfig:
    emit_snapshot: bool = True
    snapshot_stage: str = ProjectStage.DRAFT.value
    fill_placeholders_via_llm: bool = True
    max_placeholders_to_fill: int = 8
    abort_on_b3_blocking: bool = True


# ============================================================
# 4. B6 COMMANDER BRAIN
# ============================================================

class B6Commander(FactoryBrain):
    BRAIN_ID = "B6_v6"
    BRAIN_NAME = "Commander"
    BRAIN_STAGE = BrainStage.COMMAND
    REQUIRED_CONTEXT_ATTRS = ("component_catalog",)

    def __init__(
        self,
        hooks=None,
        config: Optional[CommanderConfig] = None,
        b1: Optional[B1IntentIngestor] = None,
        b2: Optional[B2ComponentScout] = None,
        b3: Optional[B3DesignCritic] = None,
        b4: Optional[B4CompositionSynthesizer] = None,
    ):
        super().__init__(hooks=hooks)
        self._config = config or CommanderConfig()
        self._b1 = b1 or B1IntentIngestor()
        self._b2 = b2 or B2ComponentScout()
        self._b3 = b3 or B3DesignCritic()
        self._b4 = b4 or B4CompositionSynthesizer()

    @enforce_principle_v6(PrincipleV6.NT1_MULTI_AXIS_CONVERGENCE)
    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def execute(self, context: FactoryBrainContext) -> FactoryBrainResult:
        orchestration_log: List[Dict[str, Any]] = []
        warnings: List[str] = []
        errors: List[str] = []
        total_llm_calls = 0

        # --- B1 ---
        r1 = self._b1.run(context)
        orchestration_log.append({"brain": "B1", "success": r1.success, "elapsed_ms": r1.elapsed_ms})
        if not r1.success:
            return self._fail("B1 failed", errors + list(r1.errors), orchestration_log)

        # --- B2 ---
        r2 = self._b2.run(context)
        orchestration_log.append({"brain": "B2", "success": r2.success, "elapsed_ms": r2.elapsed_ms})
        if not r2.success:
            return self._fail("B2 failed", list(r2.errors), orchestration_log)
        warnings.extend(r2.warnings)

        # --- B3 ---
        r3 = self._b3.run(context)
        orchestration_log.append({"brain": "B3", "success": r3.success, "elapsed_ms": r3.elapsed_ms})
        if r3.success and r3.outputs.get("is_blocking") and self._config.abort_on_b3_blocking:
            # Check C2 override
            if not context.shared_memory.get("c2_override_blocking", False):
                warnings.append("B3 blocking - commander abort per config")
                return self._fail("b3_blocking_no_override", [], orchestration_log)

        # --- B4 ---
        r4 = self._b4.run(context)
        orchestration_log.append({"brain": "B4", "success": r4.success, "elapsed_ms": r4.elapsed_ms})
        if not r4.success:
            return self._fail("B4 failed", list(r4.errors), orchestration_log)

        # --- Borrowing Protocol: fill placeholders ---
        if self._config.fill_placeholders_via_llm and context.has_llm():
            borrow_stats = self._fill_placeholders(context)
            total_llm_calls += borrow_stats["llm_calls"]
            orchestration_log.append({"brain": "borrow", **borrow_stats})
            warnings.extend(borrow_stats.get("warnings", []))

        # --- Emit Snapshot ---
        emitted_snapshot_id: Optional[str] = None
        if self._config.emit_snapshot and context.active_design_graph is not None:
            snap = snapshot_from_factory_result(
                context,
                FactoryBrainResult(brain_id=self.BRAIN_ID, success=True, outputs={}),
                snapshot_id=f"snap_{uuid.uuid4().hex[:12]}",
                version_label="v1",
                stage_tag=self._config.snapshot_stage,
            )
            if snap is not None and context.snapshot_lineage is not None:
                context.snapshot_lineage.append(snap)
                context.snapshot_lineage.set_head(snap.snapshot_id)
                emitted_snapshot_id = snap.snapshot_id
                orchestration_log.append({"brain": "snapshot", "snapshot_id": snap.snapshot_id})

        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs={
                "orchestration_log": orchestration_log,
                "active_graph_id": context.active_design_graph.graph_id if context.active_design_graph else None,
                "variants_count": len(context.variant_graphs),
                "emitted_snapshot_id": emitted_snapshot_id,
            },
            warnings=warnings,
            metrics={
                "total_llm_calls": float(total_llm_calls),
                "brains_run": float(len([x for x in orchestration_log if "brain" in x])),
            },
            stage=self.BRAIN_STAGE.value,
            emitted_snapshot_id=emitted_snapshot_id,
            llm_calls=total_llm_calls,
        )

    def _fill_placeholders(self, context: FactoryBrainContext) -> Dict[str, Any]:
        """Duyệt placeholder trong active graph, gọi Borrowing Protocol."""
        if context.active_design_graph is None:
            return {"llm_calls": 0, "filled": 0, "warnings": []}

        graph = context.active_design_graph
        protocol = BorrowingProtocol(context.llm_broker)
        filled = 0
        llm_calls = 0
        warnings: List[str] = []

        placeholders = [
            (nid, n) for nid, n in graph.nodes.items()
            if n.metadata.get("needs_llm_fill") and n.component_id.startswith("placeholder.")
        ][: self._config.max_placeholders_to_fill]

        for node_id, node in placeholders:
            feature_id = node.metadata.get("feature_id", "unknown")
            prompt = self._build_fill_prompt(context, feature_id)
            request = BorrowRequest(
                request_id=f"fill_{feature_id}_{uuid.uuid4().hex[:8]}",
                purpose=f"fill_placeholder_{feature_id}",
                prompt=prompt,
                schema=PLACEHOLDER_FILL_SCHEMA,
                temperature=0.2,
                max_retries=2,
            )
            result = protocol.borrow(request)
            llm_calls += result.llm_calls
            if result.success and result.output:
                node.component_id = result.output["component_id"]
                node.props.update(result.output.get("props", {}))
                node.metadata["needs_llm_fill"] = False
                node.metadata["llm_rationale"] = result.output.get("rationale", "")
                filled += 1
            else:
                warnings.append(
                    f"Borrow fail cho '{feature_id}': {'; '.join(result.errors[:2])}"
                )
        return {"llm_calls": llm_calls, "filled": filled, "warnings": warnings}

    def _build_fill_prompt(self, context: FactoryBrainContext, feature_id: str) -> str:
        brief = context.require_brief()
        # Prompt khung hóa - không đưa brief raw vào
        return (
            f"Propose a React + TypeScript + Tailwind component to fill the '{feature_id}' "
            f"slot of a {brief.product_type} with tone {list(brief.tone)}. "
            f"Constraints: language={brief.language}, a11y=WCAG AA. "
            f"Output JSON strictly matching the provided schema. "
            f"component_id must follow pattern: <category>.<family>.<variant>"
        )

    def _fail(
        self,
        reason: str,
        errors: List[str],
        log: List[Dict[str, Any]],
    ) -> FactoryBrainResult:
        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=False,
            outputs={"orchestration_log": log, "failure_reason": reason},
            errors=errors,
            stage=self.BRAIN_STAGE.value,
        )


# ============================================================
# 5. SANITY CHECK
# ============================================================

def b6_commander_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ontology_ui import ComponentCatalog

    checks: Dict[str, bool] = {}

    ctx = FactoryBrainContext(
        run_id="r", current_date="2025-01-01", draws=[], current_idx=0,
        project_id="p_test",
        component_catalog=ComponentCatalog(),
        shared_memory={"raw_brief": "Landing page tối giản có navbar hero cta footer, bundle 250kb"},
    )
    result = B6Commander().run(ctx)
    checks["run_success"] = result.success
    checks["active_graph_exists"] = ctx.active_design_graph is not None
    checks["variants_produced"] = len(ctx.variant_graphs) == 3
    log = result.outputs.get("orchestration_log", [])
    checks["b1_b2_b3_b4_ran"] = {"B1", "B2", "B3", "B4"} <= {e.get("brain") for e in log}

    # Schema Guard smoke
    try:
        SchemaGuard.validate(
            {"component_id": "x.y.z", "props": {}, "rationale": "ok"},
            PLACEHOLDER_FILL_SCHEMA,
        )
        checks["schema_ok"] = True
    except Exception:
        checks["schema_ok"] = False

    try:
        SchemaGuard.validate({"component_id": 123}, PLACEHOLDER_FILL_SCHEMA)
        checks["schema_rejects"] = False
    except SchemaGuardError:
        checks["schema_rejects"] = True

    return checks


__all__ = [
    "B6_VERSION", "SchemaGuard", "SchemaGuardError",
    "BorrowRequest", "BorrowResult", "PLACEHOLDER_FILL_SCHEMA", "BorrowingProtocol",
    "CommanderConfig", "B6Commander", "b6_commander_sanity_check",
]
