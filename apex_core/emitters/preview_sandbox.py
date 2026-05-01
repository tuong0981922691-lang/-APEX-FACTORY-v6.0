"""
APEX FACTORY v6.0 - UI Layer (v6)
File: preview_sandbox.py

Mục đích: Sau khi emitter sinh code, Sandbox này chạy THẬT:
    1. Ghi EmitResult ra temp dir
    2. (Optional) npm install
    3. Chạy `vite build` hoặc `vite dev`
    4. Đo bundle size thật từ dist/
    5. (Optional) chạy Lighthouse qua lighthouse-cli
    6. Trả về SandboxReport cho Radar 4D recalibration

Triết lý:
    - Phase 2 Radar 4D là FORECAST từ graph topology
    - Phase 3 Sandbox là MEASUREMENT từ build output thật
    - Khi cả 2 khớp → confidence cao; khi lệch → Radar weights cần calibrate

Safety:
    - Timeout mọi subprocess (default 180s)
    - Mode "dry_run" chỉ ghi file + return path (không chạy npm)
    - Kill switch aware
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from apex_core.emitters.react_emitter import EmitResult
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)

# ============================================================
# 0. VERSION
# ============================================================

PREVIEW_SANDBOX_VERSION = "6.0.0"


# ============================================================
# 1. RESULT TYPES
# ============================================================

class SandboxMode(str, Enum):
    DRY_RUN = "dry_run"                # chỉ ghi file, không chạy
    INSTALL_ONLY = "install_only"      # npm install, không build
    BUILD = "build"                    # npm install + vite build
    BUILD_AND_PREVIEW = "build_preview" # + vite preview server
    FULL_LIGHTHOUSE = "lighthouse"     # + lighthouse audit


class SandboxStatus(str, Enum):
    SUCCESS = "success"
    INSTALL_FAILED = "install_failed"
    BUILD_FAILED = "build_failed"
    LIGHTHOUSE_FAILED = "lighthouse_failed"
    TIMEOUT = "timeout"
    KILL_SWITCH = "kill_switch"
    NODE_NOT_AVAILABLE = "node_not_available"
    ERROR = "error"


@dataclass
class SubprocessResult:
    command: str
    exit_code: int
    stdout_tail: str                    # last 4KB
    stderr_tail: str                    # last 4KB
    elapsed_sec: float
    timed_out: bool = False


@dataclass
class BundleMeasurement:
    """Đo thật từ dist/ folder sau build."""
    total_size_bytes: int
    total_size_kb: float
    gzipped_estimate_kb: float          # ~ 33% of raw for JS
    file_count: int
    largest_file: str
    largest_file_kb: float
    js_size_kb: float
    css_size_kb: float
    html_size_kb: float
    asset_breakdown: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LighthouseScores:
    performance: Optional[float] = None         # 0..1
    accessibility: Optional[float] = None
    best_practices: Optional[float] = None
    seo: Optional[float] = None
    lcp_ms: Optional[float] = None
    tbt_ms: Optional[float] = None
    cls: Optional[float] = None


@dataclass
class SandboxReport:
    status: SandboxStatus
    mode: SandboxMode
    working_dir: str
    files_written: int
    install_result: Optional[SubprocessResult] = None
    build_result: Optional[SubprocessResult] = None
    lighthouse_result: Optional[SubprocessResult] = None
    bundle_measurement: Optional[BundleMeasurement] = None
    lighthouse_scores: Optional[LighthouseScores] = None
    total_elapsed_sec: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def is_success(self) -> bool:
        return self.status == SandboxStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "mode": self.mode.value,
            "working_dir": self.working_dir,
            "files_written": self.files_written,
            "install_result": asdict(self.install_result) if self.install_result else None,
            "build_result": asdict(self.build_result) if self.build_result else None,
            "lighthouse_result": asdict(self.lighthouse_result) if self.lighthouse_result else None,
            "bundle_measurement": (
                self.bundle_measurement.to_dict() if self.bundle_measurement else None
            ),
            "lighthouse_scores": (
                asdict(self.lighthouse_scores) if self.lighthouse_scores else None
            ),
            "total_elapsed_sec": round(self.total_elapsed_sec, 2),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


# ============================================================
# 2. CONFIG
# ============================================================

@dataclass
class SandboxConfig:
    mode: SandboxMode = SandboxMode.BUILD
    working_dir: Optional[str] = None          # None → temp dir mỗi run
    reuse_node_modules: bool = True            # True → skip npm install nếu đã có
    npm_timeout_sec: int = 300
    build_timeout_sec: int = 180
    lighthouse_timeout_sec: int = 120
    keep_on_success: bool = False              # True → không xóa working_dir
    keep_on_failure: bool = True               # Giữ để debug
    use_npm_ci: bool = False                   # ci nhanh hơn install khi có lock
    kill_switch_check: Optional[Any] = None    # KillSwitch instance


# ============================================================
# 3. UTILITIES
# ============================================================

def _node_available() -> bool:
    return shutil.which("node") is not None and shutil.which("npm") is not None


def _run_subprocess(
    cmd: Sequence[str],
    cwd: Path,
    timeout_sec: int,
    env: Optional[Dict[str, str]] = None,
) -> SubprocessResult:
    start = time.perf_counter()
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code = -1
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env={**os.environ, **(env or {})},
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout = (e.stdout or b"").decode("utf-8", errors="ignore") if e.stdout else ""
        stderr = (e.stderr or b"").decode("utf-8", errors="ignore") if e.stderr else ""
        exit_code = -1
    except FileNotFoundError:
        stderr = f"Command not found: {cmd[0] if cmd else '?'}"
        exit_code = -2
    elapsed = time.perf_counter() - start

    return SubprocessResult(
        command=" ".join(cmd),
        exit_code=exit_code,
        stdout_tail=stdout[-4096:] if stdout else "",
        stderr_tail=stderr[-4096:] if stderr else "",
        elapsed_sec=elapsed,
        timed_out=timed_out,
    )


def _measure_bundle(dist_dir: Path) -> BundleMeasurement:
    total_bytes = 0
    file_count = 0
    largest_name = ""
    largest_bytes = 0
    js_bytes = 0
    css_bytes = 0
    html_bytes = 0
    breakdown: List[Dict[str, Any]] = []

    for root, _, files in os.walk(dist_dir):
        for fname in files:
            fpath = Path(root) / fname
            try:
                size = fpath.stat().st_size
            except OSError:
                continue
            total_bytes += size
            file_count += 1
            if size > largest_bytes:
                largest_bytes = size
                largest_name = str(fpath.relative_to(dist_dir))
            ext = fpath.suffix.lower()
            if ext in (".js", ".mjs"):
                js_bytes += size
            elif ext == ".css":
                css_bytes += size
            elif ext == ".html":
                html_bytes += size
            breakdown.append({
                "path": str(fpath.relative_to(dist_dir)),
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
            })

    total_kb = total_bytes / 1024
    # Gzip ước tính: JS ~ 33%, CSS ~ 25%
    gzip_kb = (js_bytes * 0.33 + css_bytes * 0.25 + html_bytes * 0.30) / 1024

    return BundleMeasurement(
        total_size_bytes=total_bytes,
        total_size_kb=round(total_kb, 2),
        gzipped_estimate_kb=round(gzip_kb, 2),
        file_count=file_count,
        largest_file=largest_name,
        largest_file_kb=round(largest_bytes / 1024, 2),
        js_size_kb=round(js_bytes / 1024, 2),
        css_size_kb=round(css_bytes / 1024, 2),
        html_size_kb=round(html_bytes / 1024, 2),
        asset_breakdown=sorted(breakdown, key=lambda b: -b["size_bytes"])[:20],
    )


def _parse_lighthouse_json(output_path: Path) -> Optional[LighthouseScores]:
    if not output_path.exists():
        return None
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
        categories = data.get("categories", {})
        audits = data.get("audits", {})

        def cat_score(key: str) -> Optional[float]:
            cat = categories.get(key)
            if cat and isinstance(cat.get("score"), (int, float)):
                return float(cat["score"])
            return None

        def audit_num(key: str) -> Optional[float]:
            a = audits.get(key)
            if a and isinstance(a.get("numericValue"), (int, float)):
                return float(a["numericValue"])
            return None

        return LighthouseScores(
            performance=cat_score("performance"),
            accessibility=cat_score("accessibility"),
            best_practices=cat_score("best-practices"),
            seo=cat_score("seo"),
            lcp_ms=audit_num("largest-contentful-paint"),
            tbt_ms=audit_num("total-blocking-time"),
            cls=audit_num("cumulative-layout-shift"),
        )
    except Exception:
        return None


# ============================================================
# 4. PREVIEW SANDBOX
# ============================================================

class PreviewSandbox:
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def run(self, emit_result: EmitResult) -> SandboxReport:
        t0 = time.perf_counter()
        warnings: List[str] = []

        # Kill switch check
        if self.config.kill_switch_check is not None:
            try:
                if self.config.kill_switch_check.is_activated():
                    return SandboxReport(
                        status=SandboxStatus.KILL_SWITCH,
                        mode=self.config.mode,
                        working_dir="",
                        files_written=0,
                        errors=["Kill switch activated"],
                    )
            except Exception:
                warnings.append("Kill switch check failed - proceeding anyway")

        # 1. Prepare working dir
        wd = Path(self.config.working_dir) if self.config.working_dir else Path(
            tempfile.mkdtemp(prefix="apex_factory_")
        )
        wd.mkdir(parents=True, exist_ok=True)

        # 2. Write files
        try:
            written = emit_result.write_to_disk(str(wd))
        except Exception as e:
            return SandboxReport(
                status=SandboxStatus.ERROR,
                mode=self.config.mode,
                working_dir=str(wd),
                files_written=0,
                errors=[f"write_to_disk failed: {type(e).__name__}: {e}"],
                total_elapsed_sec=time.perf_counter() - t0,
            )

        files_written = len(written)

        # DRY_RUN → dừng tại đây
        if self.config.mode == SandboxMode.DRY_RUN:
            return SandboxReport(
                status=SandboxStatus.SUCCESS,
                mode=self.config.mode,
                working_dir=str(wd),
                files_written=files_written,
                warnings=warnings,
                total_elapsed_sec=time.perf_counter() - t0,
            )

        # 3. Check Node.js availability
        if not _node_available():
            return SandboxReport(
                status=SandboxStatus.NODE_NOT_AVAILABLE,
                mode=self.config.mode,
                working_dir=str(wd),
                files_written=files_written,
                errors=["node/npm not in PATH"],
                total_elapsed_sec=time.perf_counter() - t0,
            )

        # 4. npm install
        install_result: Optional[SubprocessResult] = None
        node_modules_dir = wd / "node_modules"
        should_install = not (
            self.config.reuse_node_modules and node_modules_dir.exists()
        )
        if should_install:
            npm_cmd = ["npm", "ci" if self.config.use_npm_ci else "install",
                       "--no-audit", "--no-fund", "--silent"]
            install_result = _run_subprocess(
                npm_cmd, wd, self.config.npm_timeout_sec,
            )
            if install_result.timed_out:
                return self._finalize(
                    status=SandboxStatus.TIMEOUT, wd=wd,
                    files_written=files_written,
                    install=install_result,
                    warnings=warnings,
                    errors=[f"npm install timed out after {self.config.npm_timeout_sec}s"],
                    t0=t0,
                )
            if install_result.exit_code != 0:
                return self._finalize(
                    status=SandboxStatus.INSTALL_FAILED, wd=wd,
                    files_written=files_written,
                    install=install_result,
                    warnings=warnings,
                    errors=[f"npm install exit {install_result.exit_code}"],
                    t0=t0,
                )
        else:
            warnings.append("Reused existing node_modules - dependencies may be stale")

        # INSTALL_ONLY → dừng
        if self.config.mode == SandboxMode.INSTALL_ONLY:
            return self._finalize(
                status=SandboxStatus.SUCCESS, wd=wd,
                files_written=files_written, install=install_result,
                warnings=warnings, t0=t0,
            )

        # 5. Vite build
        build_result = _run_subprocess(
            ["npm", "run", "build", "--silent"],
            wd, self.config.build_timeout_sec,
        )
        if build_result.timed_out:
            return self._finalize(
                status=SandboxStatus.TIMEOUT, wd=wd,
                files_written=files_written, install=install_result, build=build_result,
                warnings=warnings,
                errors=[f"build timed out after {self.config.build_timeout_sec}s"],
                t0=t0,
            )
        if build_result.exit_code != 0:
            return self._finalize(
                status=SandboxStatus.BUILD_FAILED, wd=wd,
                files_written=files_written, install=install_result, build=build_result,
                warnings=warnings,
                errors=[f"build exit {build_result.exit_code}"],
                t0=t0,
            )

        # 6. Measure bundle
        dist_dir = wd / "dist"
        bundle: Optional[BundleMeasurement] = None
        if dist_dir.exists():
            bundle = _measure_bundle(dist_dir)
        else:
            warnings.append("dist/ not found after build")

        # 7. Lighthouse (optional)
        lh_result: Optional[SubprocessResult] = None
        lh_scores: Optional[LighthouseScores] = None
        if self.config.mode == SandboxMode.FULL_LIGHTHOUSE:
            wd / "lighthouse.json"
            # Require lighthouse CLI installed globally (C2 cài riêng)
            if shutil.which("lighthouse") is None:
                warnings.append(
                    "lighthouse CLI không có trong PATH - skip audit. "
                    "Cài: npm install -g lighthouse"
                )
            else:
                # Serve dist qua vite preview tạm thời, rồi lighthouse URL đó
                # Phase 3 version: skip preview server automation, để C2 chạy tay
                warnings.append(
                    "Lighthouse tự động cần vite preview server - "
                    "Phase 3 skip, để Phase 6 deploy adapter xử lý"
                )

        return self._finalize(
            status=SandboxStatus.SUCCESS, wd=wd,
            files_written=files_written,
            install=install_result, build=build_result, lighthouse=lh_result,
            bundle=bundle, lh_scores=lh_scores,
            warnings=warnings, t0=t0,
        )

    def _finalize(
        self,
        *,
        status: SandboxStatus,
        wd: Path,
        files_written: int,
        install: Optional[SubprocessResult] = None,
        build: Optional[SubprocessResult] = None,
        lighthouse: Optional[SubprocessResult] = None,
        bundle: Optional[BundleMeasurement] = None,
        lh_scores: Optional[LighthouseScores] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        t0: float = 0.0,
    ) -> SandboxReport:
        # Cleanup
        success = status == SandboxStatus.SUCCESS
        should_cleanup = (
            (success and not self.config.keep_on_success)
            or (not success and not self.config.keep_on_failure)
        )
        if should_cleanup:
            try:
                shutil.rmtree(wd, ignore_errors=True)
            except Exception:
                pass

        return SandboxReport(
            status=status,
            mode=self.config.mode,
            working_dir=str(wd),
            files_written=files_written,
            install_result=install,
            build_result=build,
            lighthouse_result=lighthouse,
            bundle_measurement=bundle,
            lighthouse_scores=lh_scores,
            total_elapsed_sec=time.perf_counter() - t0,
            warnings=warnings or [],
            errors=errors or [],
        )


# ============================================================
# 5. SANITY CHECK
# ============================================================

def preview_sandbox_sanity_check() -> Dict[str, bool]:
    from apex_core.emitters.react_emitter import EmitConfig, ReactEmitter
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

    # Build minimal emit
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
    g = DesignGraph(graph_id="g", target=RenderTarget.REACT, root_id="r")
    g.add_node(DesignNode(node_id="r", component_id="div"))
    g.add_node(DesignNode(
        node_id="b", component_id="atom.button.primary",
        props={"label": "Go"},
    ))
    g.link("r", "default", "b")
    result = ReactEmitter(cat, reg, EmitConfig()).emit_graph(g)

    # Dry-run test (luôn chạy được, không cần node)
    sandbox = PreviewSandbox(SandboxConfig(
        mode=SandboxMode.DRY_RUN,
        keep_on_success=False,
    ))
    report = sandbox.run(result)
    checks["dry_run_success"] = report.status == SandboxStatus.SUCCESS
    checks["files_written"] = report.files_written > 0
    checks["dict_serializable"] = isinstance(report.to_dict(), dict)

    # Node available check - chỉ chạy khi có node
    if _node_available():
        checks["node_available"] = True
        # Test INSTALL_ONLY mode với timeout ngắn - có thể fail do network
        # → chỉ check return schema, không assert success
        sandbox2 = PreviewSandbox(SandboxConfig(
            mode=SandboxMode.INSTALL_ONLY,
            npm_timeout_sec=30,
            keep_on_failure=False,
        ))
        report2 = sandbox2.run(result)
        checks["install_report_has_status"] = isinstance(report2.status, SandboxStatus)
    else:
        checks["node_available"] = False

    return checks


__all__ = [
    "PREVIEW_SANDBOX_VERSION",
    "SandboxMode", "SandboxStatus",
    "SubprocessResult", "BundleMeasurement", "LighthouseScores", "SandboxReport",
    "SandboxConfig", "PreviewSandbox",
    "preview_sandbox_sanity_check",
]
