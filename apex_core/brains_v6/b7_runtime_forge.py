"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: b7_runtime_forge.py

Vai trò B7: RUNTIME FORGE (SKELETON - Phase 4 implement đầy đủ)
    Ở Phase 1, B7 chỉ ship:
      - ErrorLedger     : Sổ Cái Lỗi Bất Biến - SHA-256, append-only
      - PatchProposal   : schema cho đề xuất vá
      - B7RuntimeForge  : brain interface + capability-token gate

Hot-inject AST thực tế (WebContainer/HMR) nằm ở Phase 4.
NT5 ENFORCED: mọi patch proposal → PENDING_C2_APPROVAL, không bao giờ
              auto-inject vào production nếu thiếu Capability Token.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

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
from apex_core.foundation.ui_ir import DesignGraph, diff_graphs
from apex_core.legacy.foundation.capability_token import CapabilityToken

# ============================================================
# 0. VERSION
# ============================================================

B7_VERSION = "6.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 1. ERROR LEDGER (append-only crash log)
# ============================================================

class ErrorKind(str, Enum):
    RUNTIME_EXCEPTION = "runtime_exception"
    RENDER_FAILURE = "render_failure"
    MEMORY_OVERFLOW = "memory_overflow"
    BUILD_FAILURE = "build_failure"
    LINT_VIOLATION = "lint_violation"
    A11Y_VIOLATION = "a11y_violation"
    PERFORMANCE_REGRESSION = "performance_regression"
    BORROW_FAILURE = "borrow_failure"


@dataclass(frozen=True)
class ErrorEntry:
    entry_id: str
    kind: ErrorKind
    message: str
    stack_trace: str
    context_hash: str                   # SHA-256 của context liên quan
    graph_id: Optional[str]
    reported_at_utc: str
    component_id: Optional[str] = None
    severity: str = "error"             # "error" | "critical" | "warning"
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            payload = {
                "entry_id": self.entry_id,
                "kind": self.kind.value,
                "message": self.message,
                "context_hash": self.context_hash,
                "graph_id": self.graph_id,
                "reported_at_utc": self.reported_at_utc,
            }
            h = hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            object.__setattr__(self, "content_hash", h)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self) | {"kind": self.kind.value}


class ErrorLedger:
    """Append-only JSONL ledger. Mọi error immutable sau khi ghi."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: ErrorEntry) -> None:
        with self.storage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def read_all(self) -> List[ErrorEntry]:
        if not self.storage_path.exists():
            return []
        entries: List[ErrorEntry] = []
        with self.storage_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    data["kind"] = ErrorKind(data["kind"])
                    entries.append(ErrorEntry(**data))
                except Exception:
                    continue
        return entries

    def count_by_kind(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.read_all():
            counts[e.kind.value] = counts.get(e.kind.value, 0) + 1
        return counts

    def recent(self, limit: int = 20) -> List[ErrorEntry]:
        entries = self.read_all()
        return entries[-limit:]


# ============================================================
# 2. PATCH PROPOSAL (Phase 4 sẽ dùng, Phase 1 chỉ define schema)
# ============================================================

class PatchStatus(str, Enum):
    DRAFT = "draft"
    PENDING_C2_APPROVAL = "pending_c2_approval"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class PatchProposal:
    proposal_id: str
    target_graph_id: str
    related_error_ids: List[str]
    graph_diff: Dict[str, Any]                  # từ GraphDiff.to_dict()
    rationale: str
    status: PatchStatus = PatchStatus.DRAFT
    created_at_utc: str = field(default_factory=_now_iso)
    c2_token_id: Optional[str] = None
    applied_at_utc: Optional[str] = None
    rolled_back_at_utc: Optional[str] = None
    rollback_reason: str = ""
    content_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "proposal_id": self.proposal_id,
            "target_graph_id": self.target_graph_id,
            "graph_diff": self.graph_diff,
            "related_error_ids": list(self.related_error_ids),
            "rationale": self.rationale,
            "created_at_utc": self.created_at_utc,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def finalize(self) -> None:
        """Gọi sau khi fill đầy đủ field để khóa hash."""
        if not self.content_hash:
            self.content_hash = self.compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target_graph_id": self.target_graph_id,
            "related_error_ids": list(self.related_error_ids),
            "graph_diff": dict(self.graph_diff),
            "rationale": self.rationale,
            "status": self.status.value,
            "created_at_utc": self.created_at_utc,
            "c2_token_id": self.c2_token_id,
            "applied_at_utc": self.applied_at_utc,
            "rolled_back_at_utc": self.rolled_back_at_utc,
            "rollback_reason": self.rollback_reason,
            "content_hash": self.content_hash,
        }


# ============================================================
# 3. AST SURGEON (skeleton - Phase 4 implement detail)
# ============================================================

class ASTSurgeon:
    """
    Phase 1: chỉ dùng graph-level diff (diff_graphs từ ui_ir).
    Phase 4: thay bằng AST diff thực trên source code React/TS.
    """

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def propose_patch(
        self,
        before: DesignGraph,
        after: DesignGraph,
        *,
        related_error_ids: Sequence[str],
        rationale: str,
    ) -> Optional[PatchProposal]:
        diff = diff_graphs(before, after)
        if diff.is_empty():
            return None
        proposal = PatchProposal(
            proposal_id=f"patch_{uuid.uuid4().hex[:12]}",
            target_graph_id=before.graph_id,
            related_error_ids=list(related_error_ids),
            graph_diff=diff.to_dict(),
            rationale=rationale,
            status=PatchStatus.PENDING_C2_APPROVAL,
        )
        proposal.finalize()
        return proposal


# ============================================================
# 4. B7 RUNTIME FORGE BRAIN
# ============================================================

class B7RuntimeForge(FactoryBrain):
    BRAIN_ID = "B7_v6"
    BRAIN_NAME = "RuntimeForge"
    BRAIN_STAGE = BrainStage.FORGE

    def __init__(
        self,
        hooks=None,
        ledger_path: Optional[Path] = None,
    ):
        super().__init__(hooks=hooks)
        self._ledger = ErrorLedger(ledger_path or Path("./apex_storage/forge/error_ledger.jsonl"))
        self._surgeon = ASTSurgeon()
        self._proposals: Dict[str, PatchProposal] = {}

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def execute(self, context: FactoryBrainContext) -> FactoryBrainResult:
        action = context.shared_memory.get("b7_action", "snapshot")

        if action == "snapshot":
            return self._snapshot()
        elif action == "record_error":
            return self._record_error_from_context(context)
        elif action == "propose_patch":
            return self._propose_patch_from_context(context)
        elif action == "list_proposals":
            return self._list_proposals()
        else:
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID, success=False, outputs={},
                errors=[f"Unknown b7_action: {action}"],
                stage=self.BRAIN_STAGE.value,
            )

    def _snapshot(self) -> FactoryBrainResult:
        counts = self._ledger.count_by_kind()
        recent = [e.to_dict() for e in self._ledger.recent(10)]
        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs={
                "ledger_counts": counts,
                "recent_errors": recent,
                "total_proposals": len(self._proposals),
                "pending_proposals": sum(
                    1 for p in self._proposals.values()
                    if p.status == PatchStatus.PENDING_C2_APPROVAL
                ),
            },
            stage=self.BRAIN_STAGE.value,
        )

    def _record_error_from_context(self, context: FactoryBrainContext) -> FactoryBrainResult:
        payload = context.shared_memory.get("error_payload", {})
        try:
            kind = ErrorKind(payload.get("kind", "runtime_exception"))
        except ValueError:
            kind = ErrorKind.RUNTIME_EXCEPTION
        entry = ErrorEntry(
            entry_id=f"err_{uuid.uuid4().hex[:12]}",
            kind=kind,
            message=str(payload.get("message", ""))[:2000],
            stack_trace=str(payload.get("stack_trace", ""))[:8000],
            context_hash=str(payload.get("context_hash", "")),
            graph_id=payload.get("graph_id"),
            component_id=payload.get("component_id"),
            severity=payload.get("severity", "error"),
            reported_at_utc=_now_iso(),
        )
        self._ledger.append(entry)
        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs={"entry_id": entry.entry_id, "kind": entry.kind.value},
            stage=self.BRAIN_STAGE.value,
        )

    def _propose_patch_from_context(self, context: FactoryBrainContext) -> FactoryBrainResult:
        before_dict = context.shared_memory.get("patch_before_graph")
        after_dict = context.shared_memory.get("patch_after_graph")
        related_errors = context.shared_memory.get("patch_related_errors", [])
        rationale = context.shared_memory.get("patch_rationale", "")

        if not before_dict or not after_dict:
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID, success=False, outputs={},
                errors=["patch_before_graph and patch_after_graph required"],
                stage=self.BRAIN_STAGE.value,
            )

        try:
            before = DesignGraph.from_dict(before_dict)
            after = DesignGraph.from_dict(after_dict)
        except Exception as e:
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID, success=False, outputs={},
                errors=[f"Invalid graph dict: {type(e).__name__}: {e}"],
                stage=self.BRAIN_STAGE.value,
            )

        proposal = self._surgeon.propose_patch(
            before=before, after=after,
            related_error_ids=related_errors, rationale=rationale,
        )
        if proposal is None:
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID, success=True,
                outputs={"proposal_id": None, "reason": "no_diff"},
                warnings=["Graphs identical - nothing to patch"],
                stage=self.BRAIN_STAGE.value,
            )
        self._proposals[proposal.proposal_id] = proposal
        return FactoryBrainResult(
            brain_id=self.BRAIN_ID, success=True,
            outputs={
                "proposal_id": proposal.proposal_id,
                "status": proposal.status.value,
                "diff_summary": proposal.graph_diff,
                "notice": "PENDING_C2_APPROVAL - cần Capability Token scope=inject_detector",
            },
            stage=self.BRAIN_STAGE.value,
        )

    def _list_proposals(self) -> FactoryBrainResult:
        items = [p.to_dict() for p in self._proposals.values()]
        return FactoryBrainResult(
            brain_id=self.BRAIN_ID, success=True,
            outputs={
                "proposals": items,
                "pending_count": sum(
                    1 for p in self._proposals.values()
                    if p.status == PatchStatus.PENDING_C2_APPROVAL
                ),
            },
            stage=self.BRAIN_STAGE.value,
        )

    # -------- Human-gated ops --------

    def c2_approve_proposal(
        self,
        proposal_id: str,
        token: CapabilityToken,
        gate: Any,       # CapabilityGate từ legacy
    ) -> Dict[str, Any]:
        """NT5: ONLY C2 + Capability Token hợp lệ mới approve được."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return {"success": False, "error": "proposal_not_found"}
        if proposal.status != PatchStatus.PENDING_C2_APPROVAL:
            return {"success": False, "error": f"invalid_status_{proposal.status.value}"}

        try:
            gate.authorize(
                token=token,
                required_scope="promote_method",
                required_resource=f"patch_proposal:{proposal_id}",
            )
        except Exception as e:
            return {"success": False, "error": f"gate_rejected: {e}"}

        proposal.status = PatchStatus.APPROVED
        proposal.c2_token_id = token.token_id
        return {"success": True, "proposal_id": proposal_id, "new_status": proposal.status.value}


# ============================================================
# 5. SANITY CHECK
# ============================================================

def b7_runtime_forge_sanity_check(tmp_path: Optional[Path] = None) -> Dict[str, bool]:
    import tempfile

    from apex_core.foundation.ui_ir import RenderTarget

    checks: Dict[str, bool] = {}

    tmp = tmp_path or Path(tempfile.mkdtemp()) / "forge_test"
    ledger_file = tmp / "errors.jsonl"

    brain = B7RuntimeForge(ledger_path=ledger_file)

    # Record error
    ctx = FactoryBrainContext(
        run_id="r", current_date="2025-01-01", draws=[], current_idx=0,
        shared_memory={
            "b7_action": "record_error",
            "error_payload": {
                "kind": "render_failure",
                "message": "useEffect infinite loop",
                "stack_trace": "at Component.render...",
                "context_hash": "abc123",
                "graph_id": "g1",
                "component_id": "organism.navbar",
            },
        },
    )
    r1 = brain.run(ctx)
    checks["record_error_ok"] = r1.success

    # Snapshot
    ctx2 = FactoryBrainContext(
        run_id="r2", current_date="2025-01-01", draws=[], current_idx=0,
        shared_memory={"b7_action": "snapshot"},
    )
    r2 = brain.run(ctx2)
    checks["snapshot_ok"] = r2.success
    checks["ledger_has_entry"] = r2.outputs["ledger_counts"].get("render_failure", 0) >= 1

    # Propose patch (no-diff)
    g = DesignGraph(graph_id="g_same", target=RenderTarget.REACT, root_id="r")
    from apex_core.foundation.ui_ir import DesignNode
    g.add_node(DesignNode(node_id="r", component_id="atom.box"))
    same = DesignGraph.from_dict(g.to_dict())
    ctx3 = FactoryBrainContext(
        run_id="r3", current_date="2025-01-01", draws=[], current_idx=0,
        shared_memory={
            "b7_action": "propose_patch",
            "patch_before_graph": g.to_dict(),
            "patch_after_graph": same.to_dict(),
            "patch_related_errors": [],
            "patch_rationale": "test",
        },
    )
    r3 = brain.run(ctx3)
    checks["no_diff_proposal"] = r3.success and r3.outputs.get("proposal_id") is None

    # Propose patch (with diff)
    after = DesignGraph.from_dict(g.to_dict())
    after.add_node(DesignNode(node_id="new", component_id="atom.button"))
    after.link("r", "default", "new")
    ctx4 = FactoryBrainContext(
        run_id="r4", current_date="2025-01-01", draws=[], current_idx=0,
        shared_memory={
            "b7_action": "propose_patch",
            "patch_before_graph": g.to_dict(),
            "patch_after_graph": after.to_dict(),
            "patch_related_errors": ["err_1"],
            "patch_rationale": "add missing button",
        },
    )
    r4 = brain.run(ctx4)
    checks["diff_proposal_created"] = r4.success and r4.outputs.get("proposal_id") is not None
    checks["proposal_is_pending"] = r4.outputs.get("status") == PatchStatus.PENDING_C2_APPROVAL.value

    return checks


__all__ = [
    "B7_VERSION",
    "ErrorKind", "ErrorEntry", "ErrorLedger",
    "PatchStatus", "PatchProposal", "ASTSurgeon",
    "B7RuntimeForge", "b7_runtime_forge_sanity_check",
]
