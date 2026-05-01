"""
APEX FACTORY v6.0 - Evolution Layer (v6)
File: hot_inject.py

Mục đích: Tiêm patch vào runtime thật. Đây là "đòn tay" cuối cùng của Forge.

    Pipeline:
      1. C2 ký Capability Token (scope="hot_inject")
      2. HotInjectEngine authorize token qua CapabilityGate legacy
      3. Snapshot state trước inject (pre_snapshot)
      4. Apply Patch (ASTSurgeonV6) → new_graph
      5. Re-emit code (ReactEmitter) → new deployment
      6. Trigger runtime reload theo strategy:
          - HMR            : ghi file + Vite tự hot-reload
          - ROLLING_RESTART: kill + spawn process mới
          - BLUE_GREEN     : swap symlink giữa 2 dir
      7. RolloutMonitor theo dõi error rate N giây sau inject
      8. Nếu error rate tăng → auto-rollback via inverse patch
      9. Snapshot state sau inject (post_snapshot)

Triết lý NT5 (Human Supremacy):
    KHÔNG có đường tắt. Mọi inject bắt buộc Capability Token hợp lệ.
    Kill switch có thể chặn giữa chừng.
"""
from __future__ import annotations

import json
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from apex_core.emitters.react_emitter import EmitResult, ReactEmitter
from apex_core.evolution_v6.ast_surgeon_v6 import (
    ASTSurgeonV6,
    Patch,
)
from apex_core.evolution_v6.error_ledger_v6 import (
    ErrorLedgerV6,
    LedgerQuery,
)
from apex_core.foundation.ontology_ui import ComponentCatalog, TokenRegistry
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.project_snapshot import (
    ProjectLineage,
    ProjectSnapshot,
    ProjectStage,
    build_snapshot_from_design_graph,
)
from apex_core.foundation.ui_ir import DesignGraph
from apex_core.legacy.foundation.capability_token import (
    CapabilityGate,
    CapabilityToken,
    KillSwitch,
)

# ============================================================
# 0. VERSION
# ============================================================

HOT_INJECT_VERSION = "6.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 1. ENUMS
# ============================================================

class InjectStrategy(str, Enum):
    HMR = "hmr"                         # Vite HMR - rẻ nhất, cần dev server chạy
    ROLLING_RESTART = "rolling_restart" # kill + respawn
    BLUE_GREEN = "blue_green"           # 2 dir, swap symlink
    FILE_ONLY = "file_only"             # chỉ ghi file, không trigger reload


class InjectMode(str, Enum):
    FULL = "full"                       # apply 100% traffic
    CANARY = "canary"                   # apply % traffic


class InjectStatus(str, Enum):
    SUCCESS = "success"
    VALIDATION_FAILED = "validation_failed"
    APPLY_FAILED = "apply_failed"
    EMIT_FAILED = "emit_failed"
    DEPLOY_FAILED = "deploy_failed"
    ROLLED_BACK = "rolled_back"
    AUTH_DENIED = "auth_denied"
    KILL_SWITCH = "kill_switch"
    TIMEOUT = "timeout"


# ============================================================
# 2. REQUEST + RESULT
# ============================================================

@dataclass
class InjectRequest:
    request_id: str
    patch: Patch
    target_graph: DesignGraph
    project_id: str
    strategy: InjectStrategy = InjectStrategy.HMR
    mode: InjectMode = InjectMode.FULL
    canary_percentage: int = 10                 # 0-100, chỉ dùng khi CANARY
    monitor_window_sec: int = 30
    auto_rollback_on_spike: bool = True
    error_spike_threshold: float = 2.0          # post_rate / pre_rate
    deployment_dir: Optional[str] = None        # path dir đích; None → temp
    notes: str = ""


@dataclass
class RolloutMetrics:
    pre_inject_error_rate: float                # errors per 60s
    post_inject_error_rate: float
    spike_ratio: float
    new_errors_seen: int
    critical_errors_seen: int
    monitor_duration_sec: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InjectResult:
    request_id: str
    status: InjectStatus
    strategy: InjectStrategy
    mode: InjectMode
    pre_snapshot_id: Optional[str] = None
    post_snapshot_id: Optional[str] = None
    new_graph_id: Optional[str] = None
    inverse_patch: Optional[Patch] = None
    rollout_metrics: Optional[RolloutMetrics] = None
    deployment_dir: Optional[str] = None
    files_written: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    elapsed_sec: float = 0.0
    started_at_utc: str = ""
    finished_at_utc: str = ""
    c2_token_id: Optional[str] = None

    def is_success(self) -> bool:
        return self.status == InjectStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "strategy": self.strategy.value,
            "mode": self.mode.value,
            "pre_snapshot_id": self.pre_snapshot_id,
            "post_snapshot_id": self.post_snapshot_id,
            "new_graph_id": self.new_graph_id,
            "inverse_patch_id": self.inverse_patch.patch_id if self.inverse_patch else None,
            "rollout_metrics": (
                self.rollout_metrics.to_dict() if self.rollout_metrics else None
            ),
            "deployment_dir": self.deployment_dir,
            "files_written": self.files_written,
            "error_message": self.error_message,
            "warnings": list(self.warnings),
            "elapsed_sec": round(self.elapsed_sec, 2),
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "c2_token_id": self.c2_token_id,
        }


# ============================================================
# 3. ROLLOUT MONITOR
# ============================================================

class RolloutMonitor:
    """Đo error rate trước/sau inject qua ErrorLedger."""

    def __init__(self, ledger: ErrorLedgerV6):
        self.ledger = ledger

    def capture_baseline(self, window_sec: int = 60) -> Tuple[int, int]:
        """
        Return (total_errors, critical_errors) trong window_sec gần nhất.
        """
        cutoff = datetime.now(timezone.utc).timestamp() - window_sec
        cutoff_iso = datetime.fromtimestamp(
            cutoff, tz=timezone.utc
        ).isoformat()
        entries = self.ledger.query(LedgerQuery(
            since_utc=cutoff_iso, limit=10000,
        ))
        critical = sum(
            1 for e in entries
            if e.severity.lower() in ("critical", "fatal")
        )
        return len(entries), critical

    def monitor_rollout(
        self,
        monitor_window_sec: int,
        pre_errors_per_min: float,
        poll_interval_sec: float = 5.0,
    ) -> Tuple[int, int, float]:
        """
        Theo dõi từ lúc inject xong. Trả (total_new_errors, critical, elapsed).
        """
        start = time.time()
        elapsed = 0.0
        total_new = 0
        total_critical = 0
        baseline_entry_ids: set = set(self.ledger._entries_by_id.keys())

        while elapsed < monitor_window_sec:
            time.sleep(min(poll_interval_sec, monitor_window_sec - elapsed))
            current_ids = set(self.ledger._entries_by_id.keys())
            new_ids = current_ids - baseline_entry_ids
            for eid in new_ids:
                entry = self.ledger.get_entry(eid)
                if entry is None:
                    continue
                total_new += 1
                if entry.severity.lower() in ("critical", "fatal"):
                    total_critical += 1
            baseline_entry_ids = current_ids
            elapsed = time.time() - start
        return total_new, total_critical, elapsed


# ============================================================
# 4. DEPLOYMENT DRIVERS (per strategy)
# ============================================================

class DeploymentDriver:
    STRATEGY: InjectStrategy = InjectStrategy.FILE_ONLY

    def deploy(
        self, emit_result: EmitResult, target_dir: Path,
    ) -> Tuple[bool, List[str]]:
        raise NotImplementedError


class FileOnlyDriver(DeploymentDriver):
    STRATEGY = InjectStrategy.FILE_ONLY

    def deploy(self, emit_result, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)
        written = emit_result.write_to_disk(str(target_dir))
        return True, written


class HMRDriver(DeploymentDriver):
    """
    Vite HMR: ghi file vào dir đang được dev server theo dõi.
    Vite tự detect file change + reload.
    """
    STRATEGY = InjectStrategy.HMR

    def deploy(self, emit_result, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)
        written = emit_result.write_to_disk(str(target_dir))
        # Tạo sentinel file để Vite detect HMR
        sentinel = target_dir / ".apex_hmr_trigger"
        sentinel.write_text(_now_iso(), encoding="utf-8")
        return True, written


class BlueGreenDriver(DeploymentDriver):
    """
    2 dir: target/blue/ và target/green/. Ghi vào slot đang idle, swap symlink.
    Yêu cầu: target_dir có thể tạo subdir blue/green + current symlink.
    """
    STRATEGY = InjectStrategy.BLUE_GREEN

    def deploy(self, emit_result, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)
        current_link = target_dir / "current"

        # Xác định slot idle
        current_target: Optional[Path] = None
        if current_link.is_symlink():
            try:
                current_target = Path(current_link.resolve())
            except Exception:
                current_target = None

        if current_target and current_target.name == "blue":
            idle_slot = target_dir / "green"
        else:
            idle_slot = target_dir / "blue"

        # Wipe idle + ghi file mới
        if idle_slot.exists():
            shutil.rmtree(idle_slot, ignore_errors=True)
        idle_slot.mkdir(parents=True, exist_ok=True)
        written = emit_result.write_to_disk(str(idle_slot))

        # Swap symlink atomic
        tmp_link = target_dir / ".current_new"
        if tmp_link.exists() or tmp_link.is_symlink():
            tmp_link.unlink()
        try:
            tmp_link.symlink_to(idle_slot.resolve())
            # Atomic rename trên POSIX
            tmp_link.replace(current_link)
        except OSError:
            # Windows không support symlink dễ → fallback rename dir
            if current_link.exists():
                shutil.rmtree(current_link, ignore_errors=True)
            shutil.copytree(idle_slot, current_link)

        return True, written


class RollingRestartDriver(DeploymentDriver):
    """
    Ghi file + gọi callback restart (C2 inject). Nếu không có callback → no-op.
    """
    STRATEGY = InjectStrategy.ROLLING_RESTART

    def __init__(self, restart_callback: Optional[Any] = None):
        self.restart_callback = restart_callback

    def deploy(self, emit_result, target_dir):
        target_dir.mkdir(parents=True, exist_ok=True)
        written = emit_result.write_to_disk(str(target_dir))
        if self.restart_callback is not None:
            try:
                self.restart_callback(target_dir)
            except Exception:
                return False, written
        return True, written


STRATEGY_TO_DRIVER_CLASS: Dict[InjectStrategy, type] = {
    InjectStrategy.FILE_ONLY: FileOnlyDriver,
    InjectStrategy.HMR: HMRDriver,
    InjectStrategy.BLUE_GREEN: BlueGreenDriver,
    InjectStrategy.ROLLING_RESTART: RollingRestartDriver,
}


# ============================================================
# 5. HOT INJECT ENGINE
# ============================================================

class HotInjectEngine:
    """
    Facade toàn luồng inject. NT5 ENFORCED.
    """

    REQUIRED_TOKEN_SCOPE = "hot_inject"

    def __init__(
        self,
        *,
        surgeon: ASTSurgeonV6,
        emitter: ReactEmitter,
        ledger: ErrorLedgerV6,
        capability_gate: CapabilityGate,
        kill_switch: KillSwitch,
        lineage: Optional[ProjectLineage] = None,
        component_catalog: Optional[ComponentCatalog] = None,
        token_registry: Optional[TokenRegistry] = None,
        driver_overrides: Optional[Mapping[InjectStrategy, DeploymentDriver]] = None,
    ):
        self.surgeon = surgeon
        self.emitter = emitter
        self.ledger = ledger
        self.capability_gate = capability_gate
        self.kill_switch = kill_switch
        self.lineage = lineage
        self.catalog = component_catalog
        self.registry = token_registry
        self.monitor = RolloutMonitor(ledger)

        # Lazy-init drivers per strategy (cho phép override)
        self._drivers: Dict[InjectStrategy, DeploymentDriver] = {}
        if driver_overrides:
            self._drivers.update(driver_overrides)

    def _driver_for(self, strategy: InjectStrategy) -> DeploymentDriver:
        if strategy in self._drivers:
            return self._drivers[strategy]
        cls = STRATEGY_TO_DRIVER_CLASS.get(strategy)
        if cls is None:
            raise ValueError(f"No driver for strategy {strategy}")
        driver = cls()
        self._drivers[strategy] = driver
        return driver

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def inject(
        self,
        request: InjectRequest,
        token: CapabilityToken,
    ) -> InjectResult:
        started = _now_iso()
        t0 = time.perf_counter()
        warnings: List[str] = []
        result = InjectResult(
            request_id=request.request_id,
            status=InjectStatus.SUCCESS,
            strategy=request.strategy,
            mode=request.mode,
            started_at_utc=started,
        )

        # --- 0. Kill switch ---
        if self.kill_switch.is_activated():
            return self._finalize(
                result, InjectStatus.KILL_SWITCH, t0,
                error="Kill switch active - inject refused",
            )

        # --- 1. Authorize Capability Token ---
        try:
            self.capability_gate.authorize(
                token=token,
                required_scope=self.REQUIRED_TOKEN_SCOPE,
                required_resource=f"graph:{request.target_graph.graph_id}",
            )
            result.c2_token_id = token.token_id
        except Exception as e:
            return self._finalize(
                result, InjectStatus.AUTH_DENIED, t0,
                error=f"capability_token_rejected: {e}",
            )

        # --- 2. Pre-snapshot ---
        pre_snap = self._snapshot_graph(
            graph=request.target_graph,
            project_id=request.project_id,
            stage=ProjectStage.UNDER_REVIEW,
            parent_id=(
                self.lineage.head_snapshot_id if self.lineage else None
            ),
            note="pre_inject",
        )
        if pre_snap is not None and self.lineage is not None:
            self.lineage.append(pre_snap)
            result.pre_snapshot_id = pre_snap.snapshot_id

        # --- 3. Validate + apply patch ---
        validation, apply_result, inverse = self.surgeon.transact(
            request.patch, request.target_graph,
        )
        if not validation.is_valid:
            return self._finalize(
                result, InjectStatus.VALIDATION_FAILED, t0,
                error=f"patch_invalid: {list(validation.errors)[:3]}",
            )
        if apply_result is None or not apply_result.success:
            return self._finalize(
                result, InjectStatus.APPLY_FAILED, t0,
                error=(apply_result.error_message if apply_result else "apply_none"),
            )
        new_graph = apply_result.new_graph
        result.new_graph_id = new_graph.graph_id
        result.inverse_patch = inverse

        # --- 4. Re-emit code ---
        try:
            emit_result = self.emitter.emit_graph(new_graph)
        except Exception as e:
            return self._finalize(
                result, InjectStatus.EMIT_FAILED, t0,
                error=f"emit_failed: {type(e).__name__}: {e}",
            )
        warnings.extend(emit_result.warnings)

        # --- 5. Baseline error rate ---
        pre_total, pre_critical = self.monitor.capture_baseline(window_sec=60)
        pre_rate = pre_total / 60.0   # per second

        # --- 6. Deploy via driver ---
        if request.deployment_dir is None:
            import tempfile
            deploy_dir = Path(tempfile.mkdtemp(prefix="apex_inject_"))
            warnings.append(f"No deployment_dir provided - using temp {deploy_dir}")
        else:
            deploy_dir = Path(request.deployment_dir)

        # CANARY: ghi vào sub-dir có suffix canary_pct để driver lo swap theo %
        if request.mode == InjectMode.CANARY:
            deploy_dir = deploy_dir / f"canary_{request.canary_percentage}pct"
            warnings.append(
                f"Canary mode {request.canary_percentage}% - deploy to {deploy_dir}"
            )

        driver = self._driver_for(request.strategy)
        try:
            ok, written = driver.deploy(emit_result, deploy_dir)
        except Exception as e:
            return self._finalize(
                result, InjectStatus.DEPLOY_FAILED, t0,
                error=f"deploy_failed: {type(e).__name__}: {e}",
            )
        result.deployment_dir = str(deploy_dir)
        result.files_written = len(written)
        if not ok:
            return self._finalize(
                result, InjectStatus.DEPLOY_FAILED, t0,
                error="driver.deploy returned False",
            )

        # --- 7. Monitor rollout + auto-rollback ---
        if request.monitor_window_sec > 0:
            new_errors, critical_errors, elapsed = self.monitor.monitor_rollout(
                monitor_window_sec=request.monitor_window_sec,
                pre_errors_per_min=pre_total,
            )
            post_rate = (new_errors / elapsed) if elapsed > 0 else 0.0
            spike = post_rate / pre_rate if pre_rate > 1e-9 else (
                float("inf") if new_errors > 0 else 1.0
            )
            metrics = RolloutMetrics(
                pre_inject_error_rate=round(pre_rate, 4),
                post_inject_error_rate=round(post_rate, 4),
                spike_ratio=round(min(spike, 999.0), 4),
                new_errors_seen=new_errors,
                critical_errors_seen=critical_errors,
                monitor_duration_sec=round(elapsed, 2),
            )
            result.rollout_metrics = metrics

            should_rollback = False
            rollback_reason = ""
            if critical_errors > 0:
                should_rollback = True
                rollback_reason = f"{critical_errors} critical errors during rollout"
            elif request.auto_rollback_on_spike and spike >= request.error_spike_threshold:
                should_rollback = True
                rollback_reason = (
                    f"error spike {spike:.2f}× >= threshold "
                    f"{request.error_spike_threshold}×"
                )

            if should_rollback and inverse is not None:
                warnings.append(f"Auto-rollback triggered: {rollback_reason}")
                # Apply inverse để có graph gốc
                rollback_apply = self.surgeon.applier.apply(inverse, new_graph)
                if rollback_apply.success:
                    try:
                        rollback_emit = self.emitter.emit_graph(
                            rollback_apply.new_graph
                        )
                        driver.deploy(rollback_emit, deploy_dir)
                    except Exception as e:
                        warnings.append(
                            f"Rollback emit/deploy failed: {type(e).__name__}: {e}"
                        )
                return self._finalize(
                    result, InjectStatus.ROLLED_BACK, t0,
                    error=rollback_reason,
                    extra_warnings=warnings,
                )

        # --- 8. Post-snapshot ---
        post_snap = self._snapshot_graph(
            graph=new_graph,
            project_id=request.project_id,
            stage=ProjectStage.DEPLOYED,
            parent_id=result.pre_snapshot_id,
            note="post_inject",
        )
        if post_snap is not None and self.lineage is not None:
            self.lineage.append(post_snap)
            self.lineage.set_head(post_snap.snapshot_id)
            result.post_snapshot_id = post_snap.snapshot_id

        return self._finalize(
            result, InjectStatus.SUCCESS, t0,
            extra_warnings=warnings,
        )

    # ---- C2 manual rollback (ngoài auto) ----

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def c2_rollback(
        self,
        inject_result: InjectResult,
        graph_after_inject: DesignGraph,
        token: CapabilityToken,
    ) -> InjectResult:
        """
        C2 chủ động rollback 1 inject đã success bằng inverse patch.
        """
        if inject_result.inverse_patch is None:
            res = InjectResult(
                request_id=f"rollback_{inject_result.request_id}",
                status=InjectStatus.APPLY_FAILED,
                strategy=inject_result.strategy,
                mode=inject_result.mode,
                error_message="no_inverse_patch_available",
                started_at_utc=_now_iso(),
            )
            return res

        rollback_req = InjectRequest(
            request_id=f"rollback_{inject_result.request_id}",
            patch=inject_result.inverse_patch,
            target_graph=graph_after_inject,
            project_id=inject_result.request_id,   # approx
            strategy=inject_result.strategy,
            mode=InjectMode.FULL,
            monitor_window_sec=0,                  # không monitor
            auto_rollback_on_spike=False,
            deployment_dir=inject_result.deployment_dir,
            notes=f"Manual rollback of {inject_result.request_id}",
        )
        return self.inject(rollback_req, token)

    # ---- helpers ----

    def _snapshot_graph(
        self,
        *,
        graph: DesignGraph,
        project_id: str,
        stage: ProjectStage,
        parent_id: Optional[str],
        note: str,
    ) -> Optional[ProjectSnapshot]:
        if self.catalog is None or self.registry is None:
            return None
        return build_snapshot_from_design_graph(
            project_id=project_id,
            snapshot_id=f"snap_{note}_{uuid.uuid4().hex[:10]}",
            version_label=f"v-{note}",
            domain="web",
            graph=graph,
            brief_hash="",
            brief_summary=f"Hot inject snapshot - {note}",
            parent_snapshot_id=parent_id,
            token_registry_fingerprint=self.registry.fingerprint(),
            component_catalog_fingerprint=self.catalog.fingerprint(),
            stage=stage,
            created_by="hot_inject_engine",
            tags=("hot_inject", note),
        )

    def _finalize(
        self,
        result: InjectResult,
        status: InjectStatus,
        t0: float,
        *,
        error: Optional[str] = None,
        extra_warnings: Optional[List[str]] = None,
    ) -> InjectResult:
        result.status = status
        result.elapsed_sec = time.perf_counter() - t0
        result.finished_at_utc = _now_iso()
        if error:
            result.error_message = error
        if extra_warnings:
            result.warnings.extend(extra_warnings)
        return result


# ============================================================
# 6. SANITY CHECK
# ============================================================

def hot_inject_sanity_check(tmp_path: Optional[Path] = None) -> Dict[str, bool]:
    import os
    import tempfile

    from apex_core.emitters.react_emitter import EmitConfig
    from apex_core.evolution_v6.ast_surgeon_v6 import PatchBuilder
    from apex_core.foundation.ontology_ui import (
        A11yContract,
        A11yRole,
        ColorToken,
        ComponentCatalog,
        ComponentCategory,
        ComponentSpec,
        ComponentState,
        PropSchema,
        RenderTarget,
        TokenRegistry,
        TokenRole,
    )
    from apex_core.foundation.ui_ir import DesignGraph, DesignNode

    checks: Dict[str, bool] = {}
    tmp = tmp_path or Path(tempfile.mkdtemp(prefix="hot_inject_"))

    # --- Setup ---
    # Token signer requires C2_MASTER_SECRET; set test value if missing
    if not os.environ.get("C2_MASTER_SECRET"):
        os.environ["C2_MASTER_SECRET"] = "test" * 16   # 64 chars
    from apex_core.legacy.foundation.capability_token import (
        CapabilityTokenSigner,
        NonceStore,
    )
    signer = CapabilityTokenSigner()
    nonce_store = NonceStore(tmp / "nonces.json")
    gate = CapabilityGate(signer, nonce_store)
    kill_switch = KillSwitch(tmp / "kill.flag")

    # Catalog + registry
    cat = ComponentCatalog()
    cat.register(ComponentSpec(
        component_id="atom.button.primary", label="Btn",
        category=ComponentCategory.ATOM,
        prop_schema=(PropSchema("label", "string", required=True),),
        slots=(), states=(ComponentState.DEFAULT,),
        a11y=A11yContract(
            role=A11yRole.BUTTON,
            keyboard_map=(("Enter", "activate"),),
        ),
        design_tokens_used=(), dependencies=(),
        render_targets=(RenderTarget.REACT,),
    ))
    reg = TokenRegistry()
    reg.add(ColorToken(token_id="c.p", value="#2563EB", role=TokenRole.PRIMARY))
    reg.freeze()

    # Graph + patch
    g = DesignGraph(graph_id="g_inj", target=RenderTarget.REACT, root_id="root")
    g.add_node(DesignNode(node_id="root", component_id="div"))
    g.add_node(DesignNode(
        node_id="btn", component_id="atom.button.primary",
        props={"label": "Hello"},
    ))
    g.link("root", "default", "btn")

    patch = (
        PatchBuilder(g.graph_id, "change button label")
        .set_prop("btn", "label", "Hello WORLD", previous_value="Hello")
        .build()
    )

    # Engine
    ledger = ErrorLedgerV6(tmp / "errors.jsonl")
    surgeon = ASTSurgeonV6(cat)
    emitter = ReactEmitter(cat, reg, EmitConfig(generate_scaffold=False))
    lineage = ProjectLineage(project_id="p_test")
    engine = HotInjectEngine(
        surgeon=surgeon, emitter=emitter, ledger=ledger,
        capability_gate=gate, kill_switch=kill_switch,
        lineage=lineage, component_catalog=cat, token_registry=reg,
    )

    # --- Test 1: success path ---
    token = signer.sign(
        scope="hot_inject",
        target_resource="graph:g_inj",
        ttl_seconds=600,
    )
    req = InjectRequest(
        request_id="req_001",
        patch=patch,
        target_graph=g,
        project_id="p_test",
        strategy=InjectStrategy.FILE_ONLY,
        mode=InjectMode.FULL,
        monitor_window_sec=0,             # no monitor for test speed
        deployment_dir=str(tmp / "deploy"),
    )
    result = engine.inject(req, token)
    checks["inject_success"] = result.status == InjectStatus.SUCCESS
    checks["files_written"] = result.files_written > 0
    checks["inverse_patch_present"] = result.inverse_patch is not None
    checks["pre_snapshot_created"] = result.pre_snapshot_id is not None
    checks["post_snapshot_created"] = result.post_snapshot_id is not None
    checks["lineage_has_2_snaps"] = len(lineage.snapshots) == 2

    # --- Test 2: kill switch blocks ---
    kill_switch.activate(reason="test_block")
    token2 = signer.sign(
        scope="hot_inject",
        target_resource="graph:g_inj",
        ttl_seconds=600,
    )
    req2 = InjectRequest(
        request_id="req_002", patch=patch, target_graph=g,
        project_id="p_test", strategy=InjectStrategy.FILE_ONLY,
        monitor_window_sec=0, deployment_dir=str(tmp / "deploy2"),
    )
    result2 = engine.inject(req2, token2)
    checks["kill_switch_blocks"] = result2.status == InjectStatus.KILL_SWITCH
    kill_switch.deactivate()

    # --- Test 3: wrong scope token rejected ---
    bad_token = signer.sign(
        scope="promote_method",   # sai scope
        target_resource="graph:g_inj",
        ttl_seconds=600,
    )
    req3 = InjectRequest(
        request_id="req_003", patch=patch, target_graph=g,
        project_id="p_test", strategy=InjectStrategy.FILE_ONLY,
        monitor_window_sec=0, deployment_dir=str(tmp / "deploy3"),
    )
    result3 = engine.inject(req3, bad_token)
    checks["wrong_scope_rejected"] = result3.status == InjectStatus.AUTH_DENIED

    # --- Test 4: invalid patch fails validation ---
    bad_patch = (
        PatchBuilder(g.graph_id, "try remove root")
        .remove_node("root")
        .build()
    )
    token4 = signer.sign(
        scope="hot_inject",
        target_resource="graph:g_inj",
        ttl_seconds=600,
    )
    req4 = InjectRequest(
        request_id="req_004", patch=bad_patch, target_graph=g,
        project_id="p_test", strategy=InjectStrategy.FILE_ONLY,
        monitor_window_sec=0, deployment_dir=str(tmp / "deploy4"),
    )
    result4 = engine.inject(req4, token4)
    checks["bad_patch_fails_validation"] = (
        result4.status == InjectStatus.VALIDATION_FAILED
    )

    # --- Test 5: result dict serializable ---
    try:
        json.dumps(result.to_dict(), default=str)
        checks["result_serializable"] = True
    except Exception:
        checks["result_serializable"] = False

    return checks


__all__ = [
    "HOT_INJECT_VERSION",
    "InjectStrategy", "InjectMode", "InjectStatus",
    "InjectRequest", "InjectResult", "RolloutMetrics",
    "RolloutMonitor",
    "DeploymentDriver",
    "FileOnlyDriver", "HMRDriver", "BlueGreenDriver", "RollingRestartDriver",
    "STRATEGY_TO_DRIVER_CLASS",
    "HotInjectEngine",
    "hot_inject_sanity_check",
]
