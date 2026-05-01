"""
APEX FACTORY v6.0 - Evolution Layer (v6)
File: ast_surgeon_v6.py

Mục đích: Nâng cấp ASTSurgeon Phase 1 thành surgeon thực thụ.
    Phase 1 chỉ có diff_graphs (so sánh). Phase 4 có:
      - PatchOperation: add/remove/modify/move_node, change_prop, add_binding, ...
      - Patch: sequence of operations, immutable, content-hashed
      - apply_patch(graph, patch) → new graph + audit
      - invert_patch(patch) → reverse patch (cho rollback)
      - validate_patch(patch, graph) pre-check trước khi apply
      - merge_patches(patches) gộp nhiều patch nhỏ thành 1

Triết lý NT4 (Constrained Creativity):
    Phẫu thuật chỉ được diễn ra TRONG ontology - không tạo component ngoài catalog.
    Mọi patch CHỈ giới hạn ở graph operations, không chèn thẳng code JSX.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from apex_core.foundation.ontology_ui import ComponentCatalog
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.ui_ir import (
    DesignGraph,
    DesignNode,
)

# ============================================================
# 0. VERSION
# ============================================================

AST_SURGEON_V6_VERSION = "6.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 1. PATCH OPERATION TYPES
# ============================================================

class PatchOpKind(str, Enum):
    ADD_NODE = "add_node"
    REMOVE_NODE = "remove_node"
    REPLACE_COMPONENT_ID = "replace_component_id"
    SET_PROP = "set_prop"
    REMOVE_PROP = "remove_prop"
    ADD_CHILD_LINK = "add_child_link"
    REMOVE_CHILD_LINK = "remove_child_link"
    MOVE_CHILD = "move_child"
    ADD_DATA_BINDING = "add_data_binding"
    REMOVE_DATA_BINDING = "remove_data_binding"
    SET_METADATA = "set_metadata"


@dataclass(frozen=True)
class PatchOperation:
    kind: PatchOpKind
    payload: Mapping[str, Any]
    # Snapshot giá trị cũ (nếu có) để phục vụ invert
    previous_value: Any = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind.value,
            "payload": dict(self.payload),
            "previous_value": self.previous_value,
            "notes": self.notes,
        }


# ============================================================
# 2. PATCH (immutable sequence of operations)
# ============================================================

@dataclass
class Patch:
    patch_id: str
    target_graph_id: str
    operations: List[PatchOperation]
    rationale: str
    created_at_utc: str = field(default_factory=_now_iso)
    content_hash: str = ""

    def _compute_hash(self) -> str:
        payload = {
            "patch_id": self.patch_id,
            "target_graph_id": self.target_graph_id,
            "ops": [op.to_dict() for op in self.operations],
            "rationale": self.rationale,
            "created_at_utc": self.created_at_utc,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def finalize(self) -> "Patch":
        if not self.content_hash:
            self.content_hash = self._compute_hash()
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "target_graph_id": self.target_graph_id,
            "operations": [op.to_dict() for op in self.operations],
            "rationale": self.rationale,
            "created_at_utc": self.created_at_utc,
            "content_hash": self.content_hash,
            "op_count": len(self.operations),
        }

    def is_empty(self) -> bool:
        return not self.operations


# ============================================================
# 3. VALIDATION
# ============================================================

@dataclass(frozen=True)
class ValidationReport:
    is_valid: bool
    errors: Tuple[str, ...]
    warnings: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class PatchValidator:
    """Kiểm tra patch có thể apply lên graph mà không vi phạm invariant."""

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def validate(
        self,
        patch: Patch,
        graph: DesignGraph,
        catalog: Optional[ComponentCatalog] = None,
    ) -> ValidationReport:
        errors: List[str] = []
        warnings: List[str] = []

        if patch.target_graph_id != graph.graph_id:
            errors.append(
                f"Patch target_graph_id={patch.target_graph_id} != graph.graph_id={graph.graph_id}"
            )

        # Simulate op-by-op để phát hiện conflict sớm
        simulated_node_ids: Set[str] = set(graph.nodes.keys())
        for i, op in enumerate(patch.operations):
            prefix = f"op[{i}] {op.kind.value}"
            payload = op.payload

            if op.kind == PatchOpKind.ADD_NODE:
                nid = payload.get("node_id")
                cid = payload.get("component_id")
                if not nid or not cid:
                    errors.append(f"{prefix}: thiếu node_id/component_id")
                    continue
                if nid in simulated_node_ids:
                    errors.append(f"{prefix}: node_id {nid} đã tồn tại")
                    continue
                if catalog and not cid.startswith("placeholder."):
                    if catalog.get(cid) is None:
                        warnings.append(f"{prefix}: component_id {cid} không có trong catalog")
                simulated_node_ids.add(nid)

            elif op.kind == PatchOpKind.REMOVE_NODE:
                nid = payload.get("node_id")
                if not nid or nid not in simulated_node_ids:
                    errors.append(f"{prefix}: node_id {nid} không tồn tại")
                    continue
                if nid == graph.root_id:
                    errors.append(f"{prefix}: không được xóa root")
                    continue
                simulated_node_ids.discard(nid)

            elif op.kind in (
                PatchOpKind.REPLACE_COMPONENT_ID,
                PatchOpKind.SET_PROP,
                PatchOpKind.REMOVE_PROP,
                PatchOpKind.ADD_CHILD_LINK,
                PatchOpKind.REMOVE_CHILD_LINK,
                PatchOpKind.ADD_DATA_BINDING,
                PatchOpKind.REMOVE_DATA_BINDING,
                PatchOpKind.SET_METADATA,
            ):
                nid = payload.get("node_id")
                if not nid or nid not in simulated_node_ids:
                    errors.append(f"{prefix}: node_id {nid} không tồn tại trong simulate")
                    continue
                if op.kind == PatchOpKind.ADD_CHILD_LINK:
                    child = payload.get("child_id")
                    if not child or child not in simulated_node_ids:
                        errors.append(f"{prefix}: child_id {child} không tồn tại")
                    if child == nid:
                        errors.append(f"{prefix}: tự link không hợp lệ")

            elif op.kind == PatchOpKind.MOVE_CHILD:
                child = payload.get("child_id")
                old_parent = payload.get("from_parent_id")
                new_parent = payload.get("to_parent_id")
                for label, v in (("child_id", child), ("from_parent_id", old_parent),
                                 ("to_parent_id", new_parent)):
                    if not v or v not in simulated_node_ids:
                        errors.append(f"{prefix}: {label} {v} không tồn tại")

        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )


# ============================================================
# 4. PATCH APPLIER
# ============================================================

@dataclass
class ApplyResult:
    success: bool
    new_graph: Optional[DesignGraph]
    applied_ops: int
    error_message: Optional[str] = None
    audit_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "applied_ops": self.applied_ops,
            "error_message": self.error_message,
            "audit_log": list(self.audit_log),
            "new_graph_id": self.new_graph.graph_id if self.new_graph else None,
        }


class PatchApplier:
    """Áp patch lên graph và sinh graph mới. KHÔNG mutate graph gốc."""

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def apply(self, patch: Patch, graph: DesignGraph) -> ApplyResult:
        # Deep copy để không mutate input
        new_graph = DesignGraph.from_dict(graph.to_dict())
        audit: List[Dict[str, Any]] = []

        for i, op in enumerate(patch.operations):
            try:
                self._apply_op(new_graph, op)
                audit.append({
                    "step": i,
                    "op": op.kind.value,
                    "status": "ok",
                })
            except Exception as e:
                audit.append({
                    "step": i,
                    "op": op.kind.value,
                    "status": "error",
                    "error": f"{type(e).__name__}: {e}",
                })
                return ApplyResult(
                    success=False,
                    new_graph=None,
                    applied_ops=i,
                    error_message=f"op[{i}] {op.kind.value} failed: {e}",
                    audit_log=audit,
                )

        return ApplyResult(
            success=True,
            new_graph=new_graph,
            applied_ops=len(patch.operations),
            audit_log=audit,
        )

    # ---- op implementations ----

    def _apply_op(self, g: DesignGraph, op: PatchOperation) -> None:
        p = op.payload
        if op.kind == PatchOpKind.ADD_NODE:
            node = DesignNode(
                node_id=p["node_id"],
                component_id=p["component_id"],
                props=dict(p.get("props", {})),
                data_bindings=dict(p.get("data_bindings", {})),
                event_handlers=dict(p.get("event_handlers", {})),
                metadata=dict(p.get("metadata", {})),
            )
            g.add_node(node)

        elif op.kind == PatchOpKind.REMOVE_NODE:
            nid = p["node_id"]
            # Gỡ khỏi parents trước
            for parent in g.nodes.values():
                for slot, ids in list(parent.children_by_slot.items()):
                    if nid in ids:
                        parent.children_by_slot[slot] = [c for c in ids if c != nid]
            g.nodes.pop(nid, None)

        elif op.kind == PatchOpKind.REPLACE_COMPONENT_ID:
            g.nodes[p["node_id"]].component_id = p["new_component_id"]

        elif op.kind == PatchOpKind.SET_PROP:
            g.nodes[p["node_id"]].props[p["prop_name"]] = p.get("value")

        elif op.kind == PatchOpKind.REMOVE_PROP:
            g.nodes[p["node_id"]].props.pop(p["prop_name"], None)

        elif op.kind == PatchOpKind.ADD_CHILD_LINK:
            g.link(p["node_id"], p.get("slot", "default"), p["child_id"])

        elif op.kind == PatchOpKind.REMOVE_CHILD_LINK:
            parent = g.nodes[p["node_id"]]
            slot = p.get("slot", "default")
            if slot in parent.children_by_slot:
                parent.children_by_slot[slot] = [
                    c for c in parent.children_by_slot[slot] if c != p["child_id"]
                ]
                if not parent.children_by_slot[slot]:
                    parent.children_by_slot.pop(slot)

        elif op.kind == PatchOpKind.MOVE_CHILD:
            child = p["child_id"]
            from_parent = g.nodes[p["from_parent_id"]]
            from_slot = p.get("from_slot", "default")
            to_slot = p.get("to_slot", "default")
            # Remove from old
            if from_slot in from_parent.children_by_slot:
                from_parent.children_by_slot[from_slot] = [
                    c for c in from_parent.children_by_slot[from_slot] if c != child
                ]
                if not from_parent.children_by_slot[from_slot]:
                    from_parent.children_by_slot.pop(from_slot)
            # Add to new
            g.link(p["to_parent_id"], to_slot, child)

        elif op.kind == PatchOpKind.ADD_DATA_BINDING:
            g.nodes[p["node_id"]].data_bindings[p["prop_name"]] = p["source_id"]

        elif op.kind == PatchOpKind.REMOVE_DATA_BINDING:
            g.nodes[p["node_id"]].data_bindings.pop(p["prop_name"], None)

        elif op.kind == PatchOpKind.SET_METADATA:
            g.nodes[p["node_id"]].metadata[p["key"]] = p.get("value")

        else:
            raise ValueError(f"Unknown op kind: {op.kind}")


# ============================================================
# 5. PATCH INVERTER (cho rollback)
# ============================================================

class PatchInverter:
    """
    Sinh reverse patch từ patch + snapshot state cũ.
    Mỗi op cần previous_value được capture đầy đủ khi build patch.
    """

    def invert(self, patch: Patch, original_graph: DesignGraph) -> Patch:
        reverse_ops: List[PatchOperation] = []
        # Duyệt ngược
        for op in reversed(patch.operations):
            reverse = self._invert_op(op, original_graph)
            if reverse is not None:
                reverse_ops.append(reverse)

        return Patch(
            patch_id=f"inv_{patch.patch_id}_{uuid.uuid4().hex[:8]}",
            target_graph_id=patch.target_graph_id,
            operations=reverse_ops,
            rationale=f"Inverse of {patch.patch_id}: {patch.rationale}",
        ).finalize()

    def _invert_op(
        self, op: PatchOperation, original_graph: DesignGraph
    ) -> Optional[PatchOperation]:
        p = op.payload
        if op.kind == PatchOpKind.ADD_NODE:
            return PatchOperation(
                kind=PatchOpKind.REMOVE_NODE,
                payload={"node_id": p["node_id"]},
                notes="inverse of add_node",
            )
        if op.kind == PatchOpKind.REMOVE_NODE:
            original_node = original_graph.nodes.get(p["node_id"])
            if original_node is None:
                return None
            return PatchOperation(
                kind=PatchOpKind.ADD_NODE,
                payload={
                    "node_id": original_node.node_id,
                    "component_id": original_node.component_id,
                    "props": dict(original_node.props),
                    "data_bindings": dict(original_node.data_bindings),
                    "event_handlers": dict(original_node.event_handlers),
                    "metadata": dict(original_node.metadata),
                },
                notes="inverse of remove_node",
            )
        if op.kind == PatchOpKind.REPLACE_COMPONENT_ID:
            return PatchOperation(
                kind=PatchOpKind.REPLACE_COMPONENT_ID,
                payload={
                    "node_id": p["node_id"],
                    "new_component_id": op.previous_value or p.get("old_component_id", ""),
                },
            )
        if op.kind == PatchOpKind.SET_PROP:
            # Revert về giá trị cũ; nếu previous_value == None có thể là "không có prop"
            if op.previous_value is None:
                return PatchOperation(
                    kind=PatchOpKind.REMOVE_PROP,
                    payload={"node_id": p["node_id"], "prop_name": p["prop_name"]},
                )
            return PatchOperation(
                kind=PatchOpKind.SET_PROP,
                payload={
                    "node_id": p["node_id"],
                    "prop_name": p["prop_name"],
                    "value": op.previous_value,
                },
            )
        if op.kind == PatchOpKind.REMOVE_PROP:
            if op.previous_value is None:
                return None
            return PatchOperation(
                kind=PatchOpKind.SET_PROP,
                payload={
                    "node_id": p["node_id"],
                    "prop_name": p["prop_name"],
                    "value": op.previous_value,
                },
            )
        if op.kind == PatchOpKind.ADD_CHILD_LINK:
            return PatchOperation(
                kind=PatchOpKind.REMOVE_CHILD_LINK,
                payload=dict(p),
            )
        if op.kind == PatchOpKind.REMOVE_CHILD_LINK:
            return PatchOperation(
                kind=PatchOpKind.ADD_CHILD_LINK,
                payload=dict(p),
            )
        if op.kind == PatchOpKind.MOVE_CHILD:
            return PatchOperation(
                kind=PatchOpKind.MOVE_CHILD,
                payload={
                    "child_id": p["child_id"],
                    "from_parent_id": p["to_parent_id"],
                    "from_slot": p.get("to_slot", "default"),
                    "to_parent_id": p["from_parent_id"],
                    "to_slot": p.get("from_slot", "default"),
                },
            )
        if op.kind == PatchOpKind.ADD_DATA_BINDING:
            return PatchOperation(
                kind=PatchOpKind.REMOVE_DATA_BINDING,
                payload={"node_id": p["node_id"], "prop_name": p["prop_name"]},
            )
        if op.kind == PatchOpKind.REMOVE_DATA_BINDING:
            if op.previous_value is None:
                return None
            return PatchOperation(
                kind=PatchOpKind.ADD_DATA_BINDING,
                payload={
                    "node_id": p["node_id"],
                    "prop_name": p["prop_name"],
                    "source_id": op.previous_value,
                },
            )
        if op.kind == PatchOpKind.SET_METADATA:
            if op.previous_value is None:
                return None
            return PatchOperation(
                kind=PatchOpKind.SET_METADATA,
                payload={
                    "node_id": p["node_id"],
                    "key": p["key"],
                    "value": op.previous_value,
                },
            )
        return None


# ============================================================
# 6. PATCH BUILDER + MERGER
# ============================================================

class PatchBuilder:
    """Helper DSL build patch."""

    def __init__(self, target_graph_id: str, rationale: str):
        self.target_graph_id = target_graph_id
        self.rationale = rationale
        self._ops: List[PatchOperation] = []

    def add_op(self, op: PatchOperation) -> "PatchBuilder":
        self._ops.append(op)
        return self

    def add_node(self, node_id: str, component_id: str, **kwargs) -> "PatchBuilder":
        self._ops.append(PatchOperation(
            kind=PatchOpKind.ADD_NODE,
            payload={"node_id": node_id, "component_id": component_id, **kwargs},
        ))
        return self

    def remove_node(self, node_id: str) -> "PatchBuilder":
        self._ops.append(PatchOperation(
            kind=PatchOpKind.REMOVE_NODE,
            payload={"node_id": node_id},
        ))
        return self

    def set_prop(
        self, node_id: str, prop_name: str, value: Any,
        previous_value: Any = None,
    ) -> "PatchBuilder":
        self._ops.append(PatchOperation(
            kind=PatchOpKind.SET_PROP,
            payload={"node_id": node_id, "prop_name": prop_name, "value": value},
            previous_value=previous_value,
        ))
        return self

    def link(self, parent_id: str, child_id: str, slot: str = "default") -> "PatchBuilder":
        self._ops.append(PatchOperation(
            kind=PatchOpKind.ADD_CHILD_LINK,
            payload={"node_id": parent_id, "child_id": child_id, "slot": slot},
        ))
        return self

    def build(self) -> Patch:
        return Patch(
            patch_id=f"patch_{uuid.uuid4().hex[:12]}",
            target_graph_id=self.target_graph_id,
            operations=list(self._ops),
            rationale=self.rationale,
        ).finalize()


def merge_patches(patches: Sequence[Patch], new_rationale: str = "") -> Patch:
    """Gộp nhiều patch thành 1. Phải cùng target_graph_id."""
    if not patches:
        raise ValueError("Empty patches list")
    first = patches[0]
    for p in patches[1:]:
        if p.target_graph_id != first.target_graph_id:
            raise ValueError(
                "Cannot merge patches with different target_graph_id"
            )
    all_ops: List[PatchOperation] = []
    for p in patches:
        all_ops.extend(p.operations)
    rationale = new_rationale or " | ".join(p.rationale for p in patches)
    return Patch(
        patch_id=f"merged_{uuid.uuid4().hex[:12]}",
        target_graph_id=first.target_graph_id,
        operations=all_ops,
        rationale=rationale,
    ).finalize()


# ============================================================
# 7. AST SURGEON V6 (facade)
# ============================================================

class ASTSurgeonV6:
    def __init__(self, catalog: Optional[ComponentCatalog] = None):
        self.catalog = catalog
        self.validator = PatchValidator()
        self.applier = PatchApplier()
        self.inverter = PatchInverter()

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def transact(
        self,
        patch: Patch,
        graph: DesignGraph,
    ) -> Tuple[ValidationReport, Optional[ApplyResult], Optional[Patch]]:
        """
        Workflow chuẩn: validate → apply → generate inverse patch để rollback dễ.
        Nếu validate fail → không apply.
        """
        report = self.validator.validate(patch, graph, self.catalog)
        if not report.is_valid:
            return report, None, None
        result = self.applier.apply(patch, graph)
        if not result.success:
            return report, result, None
        inverse = self.inverter.invert(patch, graph)
        return report, result, inverse


# ============================================================
# 8. SANITY CHECK
# ============================================================

def ast_surgeon_v6_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ui_ir import RenderTarget
    checks: Dict[str, bool] = {}

    # Build graph đơn giản: root + 2 children
    g = DesignGraph(graph_id="g_surg", target=RenderTarget.REACT, root_id="root")
    g.add_node(DesignNode(node_id="root", component_id="page.landing"))
    g.add_node(DesignNode(node_id="nav", component_id="organism.navbar",
                          props={"brand": "Acme"}))
    g.add_node(DesignNode(node_id="hero", component_id="organism.hero"))
    g.link("root", "main", "nav")
    g.link("root", "main", "hero")
    original_dict = g.to_dict()

    surgeon = ASTSurgeonV6()

    # 1. Add + link op
    patch = (
        PatchBuilder(g.graph_id, "add cta after hero")
        .add_node("cta1", "atom.button.primary", props={"label": "Sign up"})
        .link("root", "cta1", slot="main")
        .build()
    )
    report, result, inv = surgeon.transact(patch, g)
    checks["validation_passed"] = report.is_valid
    checks["apply_success"] = result is not None and result.success
    checks["new_node_present"] = (
        result is not None and "cta1" in result.new_graph.nodes
    )
    checks["original_unchanged"] = g.to_dict() == original_dict
    checks["inverse_generated"] = inv is not None and len(inv.operations) > 0

    # 2. Apply inverse → back to original
    if inv:
        report2, result2, _ = surgeon.transact(inv, result.new_graph)
        checks["inverse_apply_success"] = result2 is not None and result2.success
        if result2 and result2.success:
            checks["roundtrip_node_removed"] = "cta1" not in result2.new_graph.nodes

    # 3. Invalid patch (remove root)
    bad_patch = (
        PatchBuilder(g.graph_id, "try remove root")
        .remove_node("root")
        .build()
    )
    bad_report, _, _ = surgeon.transact(bad_patch, g)
    checks["remove_root_rejected"] = not bad_report.is_valid

    # 4. Merge patches
    p1 = PatchBuilder(g.graph_id, "change brand").set_prop(
        "nav", "brand", "NewBrand", previous_value="Acme"
    ).build()
    p2 = PatchBuilder(g.graph_id, "add cta").add_node(
        "cta2", "atom.button.primary", props={"label": "Buy"}
    ).link("root", "cta2").build()
    merged = merge_patches([p1, p2])
    checks["merge_ops_count"] = len(merged.operations) == 3

    # 5. Patch content hash stable
    (
        PatchBuilder(g.graph_id, "change brand")
        .set_prop("nav", "brand", "NewBrand", previous_value="Acme")
        .build()
    )
    # hash sẽ khác vì patch_id random. OK - đảm bảo compute_hash là deterministic cho patch cố định:
    manual = Patch(
        patch_id="p_fixed",
        target_graph_id=g.graph_id,
        operations=p1.operations,
        rationale="change brand",
        created_at_utc="2025-01-01T00:00:00+00:00",
    ).finalize()
    manual2 = Patch(
        patch_id="p_fixed",
        target_graph_id=g.graph_id,
        operations=p1.operations,
        rationale="change brand",
        created_at_utc="2025-01-01T00:00:00+00:00",
    ).finalize()
    checks["hash_deterministic"] = manual.content_hash == manual2.content_hash

    return checks


__all__ = [
    "AST_SURGEON_V6_VERSION",
    "PatchOpKind", "PatchOperation",
    "Patch", "PatchBuilder", "merge_patches",
    "ValidationReport", "PatchValidator",
    "ApplyResult", "PatchApplier",
    "PatchInverter",
    "ASTSurgeonV6",
    "ast_surgeon_v6_sanity_check",
]
