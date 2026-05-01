"""
APEX FACTORY v6.0 - Factory Layer
File: deploy_adapter.py

Mục đích: Đưa BuildArtifact / EmitResult lên production platform.
    Hỗ trợ 5 platform + 1 generic git push:

    1. VERCEL          : `vercel` CLI, ưu tiên cho React/Next.js
    2. CLOUDFLARE_PAGES: `wrangler pages deploy`, edge-first
    3. NETLIFY         : `netlify deploy --prod`
    4. S3_CLOUDFRONT   : aws-cli sync + invalidation
    5. GIT_PUSH        : generic, push lên remote để CI tự build
    6. LOCAL_DRY_RUN   : ghi file + log, không gọi mạng

Triết lý NT5:
    KHÔNG AUTO-DEPLOY. Mọi deploy bắt buộc Capability Token hợp lệ
    với scope="deploy". Kill Switch có thể chặn giữa chừng.

Rollback:
    Lưu previous_deployment_id trong DeployLedger. Rollback = re-deploy
    bằng previous_id qua API platform (nếu support).
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from apex_core.factories.web_factory import BuildArtifact
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.legacy.foundation.capability_token import (
    CapabilityGate,
    CapabilityToken,
    KillSwitch,
)

# ============================================================
# 0. VERSION
# ============================================================

DEPLOY_ADAPTER_VERSION = "6.0.0"
DEPLOY_TOKEN_SCOPE = "deploy"       # scope cố định


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 1. ENUMS
# ============================================================

class DeployPlatform(str, Enum):
    VERCEL = "vercel"
    CLOUDFLARE_PAGES = "cloudflare_pages"
    NETLIFY = "netlify"
    S3_CLOUDFRONT = "s3_cloudfront"
    GIT_PUSH = "git_push"
    LOCAL_DRY_RUN = "local_dry_run"


class DeployStatus(str, Enum):
    SUCCESS = "success"
    CLI_MISSING = "cli_missing"
    AUTH_DENIED = "auth_denied"
    KILL_SWITCH = "kill_switch"
    BUILD_CMD_FAILED = "build_cmd_failed"
    DEPLOY_CMD_FAILED = "deploy_cmd_failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    ROLLED_BACK = "rolled_back"


# ============================================================
# 2. DATA TYPES
# ============================================================

@dataclass
class DeployRequest:
    request_id: str
    platform: DeployPlatform
    source_dir: str                            # path chứa project đã emit
    environment: str = "production"            # "production" | "preview" | "staging"
    project_name: str = "apex-factory-app"
    domain: Optional[str] = None               # custom domain nếu có
    build_cmd: Optional[str] = None            # "npm run build"
    output_dir: str = "dist"                   # relative to source_dir
    extra_env: Dict[str, str] = field(default_factory=dict)
    timeout_sec: int = 600
    notes: str = ""


@dataclass
class CliResult:
    command: str
    exit_code: int
    stdout_tail: str
    stderr_tail: str
    elapsed_sec: float
    timed_out: bool = False


@dataclass
class DeployResult:
    request_id: str
    platform: DeployPlatform
    status: DeployStatus
    deployment_id: Optional[str] = None        # platform-specific ID
    deployment_url: Optional[str] = None
    previous_deployment_id: Optional[str] = None
    cli_results: List[CliResult] = field(default_factory=list)
    started_at_utc: str = field(default_factory=_now_iso)
    finished_at_utc: str = ""
    elapsed_sec: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    c2_token_id: Optional[str] = None

    def is_success(self) -> bool:
        return self.status == DeployStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "platform": self.platform.value,
            "status": self.status.value,
            "deployment_id": self.deployment_id,
            "deployment_url": self.deployment_url,
            "previous_deployment_id": self.previous_deployment_id,
            "cli_results": [asdict(r) for r in self.cli_results],
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "elapsed_sec": round(self.elapsed_sec, 2),
            "error_message": self.error_message,
            "warnings": list(self.warnings),
            "c2_token_id": self.c2_token_id,
        }


# ============================================================
# 3. SUBPROCESS UTIL
# ============================================================

def _run_cli(
    cmd: Sequence[str],
    cwd: Path,
    timeout_sec: int,
    env: Optional[Dict[str, str]] = None,
) -> CliResult:
    start = time.perf_counter()
    timed_out = False
    stdout_out = ""
    stderr_out = ""
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
        stdout_out = proc.stdout or ""
        stderr_out = proc.stderr or ""
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout_out = (e.stdout or b"").decode("utf-8", errors="ignore") if e.stdout else ""
        stderr_out = (e.stderr or b"").decode("utf-8", errors="ignore") if e.stderr else ""
    except FileNotFoundError:
        stderr_out = f"Command not found: {cmd[0] if cmd else '?'}"
        exit_code = -2

    return CliResult(
        command=" ".join(shlex.quote(c) for c in cmd),
        exit_code=exit_code,
        stdout_tail=stdout_out[-4096:],
        stderr_tail=stderr_out[-4096:],
        elapsed_sec=time.perf_counter() - start,
        timed_out=timed_out,
    )


def _cli_available(cmd: str) -> bool:
    return shutil.which(cmd) is not None


# ============================================================
# 4. PLATFORM DRIVER BASE + IMPLEMENTATIONS
# ============================================================

class DeployDriver:
    PLATFORM: DeployPlatform = DeployPlatform.LOCAL_DRY_RUN
    REQUIRED_CLI: Tuple[str, ...] = ()

    def is_available(self) -> bool:
        return all(_cli_available(c) for c in self.REQUIRED_CLI)

    def deploy(
        self, request: DeployRequest, result: DeployResult,
    ) -> DeployResult:
        raise NotImplementedError


# ---- LOCAL DRY RUN ----

class LocalDryRunDriver(DeployDriver):
    PLATFORM = DeployPlatform.LOCAL_DRY_RUN
    REQUIRED_CLI = ()

    def deploy(self, request, result):
        # Không thực sự deploy, chỉ ghi manifest
        src = Path(request.source_dir)
        manifest = {
            "dry_run": True,
            "platform": request.platform.value,
            "source_dir": str(src.resolve()),
            "files_scanned": sum(1 for _ in src.rglob("*") if _.is_file()) if src.exists() else 0,
            "simulated_at_utc": _now_iso(),
        }
        manifest_path = src / ".apex_deploy_dry_run.json"
        try:
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            result.warnings.append(f"manifest_write_failed: {e}")
        result.status = DeployStatus.SUCCESS
        result.deployment_id = f"dry_{uuid.uuid4().hex[:12]}"
        result.deployment_url = f"file://{src.resolve()}"
        return result


# ---- VERCEL ----

class VercelDriver(DeployDriver):
    PLATFORM = DeployPlatform.VERCEL
    REQUIRED_CLI = ("vercel",)

    def deploy(self, request, result):
        src = Path(request.source_dir)
        if not src.exists():
            result.status = DeployStatus.ERROR
            result.error_message = f"source_dir not found: {src}"
            return result

        # Build step (nếu có)
        if request.build_cmd:
            build = _run_cli(
                shlex.split(request.build_cmd),
                src, request.timeout_sec,
                env=dict(request.extra_env),
            )
            result.cli_results.append(build)
            if build.timed_out:
                result.status = DeployStatus.TIMEOUT
                result.error_message = "build_timeout"
                return result
            if build.exit_code != 0:
                result.status = DeployStatus.BUILD_CMD_FAILED
                result.error_message = f"build exit {build.exit_code}"
                return result

        # Deploy
        deploy_cmd = ["vercel", "--yes"]
        if request.environment == "production":
            deploy_cmd.append("--prod")
        if request.project_name:
            deploy_cmd.extend(["--name", request.project_name])
        deploy_cli = _run_cli(
            deploy_cmd, src, request.timeout_sec,
            env=dict(request.extra_env),
        )
        result.cli_results.append(deploy_cli)
        if deploy_cli.timed_out:
            result.status = DeployStatus.TIMEOUT
            result.error_message = "deploy_timeout"
            return result
        if deploy_cli.exit_code != 0:
            result.status = DeployStatus.DEPLOY_CMD_FAILED
            result.error_message = f"vercel exit {deploy_cli.exit_code}"
            return result

        # Parse deployment URL (Vercel prints it on last line)
        url = _extract_url_from_output(deploy_cli.stdout_tail)
        result.deployment_url = url
        result.deployment_id = url.split("://")[-1] if url else None
        result.status = DeployStatus.SUCCESS
        return result


# ---- CLOUDFLARE PAGES ----

class CloudflarePagesDriver(DeployDriver):
    PLATFORM = DeployPlatform.CLOUDFLARE_PAGES
    REQUIRED_CLI = ("wrangler",)

    def deploy(self, request, result):
        src = Path(request.source_dir)
        if not src.exists():
            result.status = DeployStatus.ERROR
            result.error_message = f"source_dir not found: {src}"
            return result

        # Build
        if request.build_cmd:
            build = _run_cli(
                shlex.split(request.build_cmd), src, request.timeout_sec,
                env=dict(request.extra_env),
            )
            result.cli_results.append(build)
            if build.exit_code != 0:
                result.status = (
                    DeployStatus.TIMEOUT if build.timed_out
                    else DeployStatus.BUILD_CMD_FAILED
                )
                result.error_message = f"build exit {build.exit_code}"
                return result

        output = src / request.output_dir
        if not output.exists():
            result.status = DeployStatus.ERROR
            result.error_message = f"output_dir not found: {output}"
            return result

        # wrangler pages deploy <dir> --project-name <name>
        deploy_cmd = [
            "wrangler", "pages", "deploy", str(output),
            "--project-name", request.project_name,
        ]
        if request.environment == "production":
            deploy_cmd.extend(["--branch", "main"])

        deploy_cli = _run_cli(
            deploy_cmd, src, request.timeout_sec,
            env=dict(request.extra_env),
        )
        result.cli_results.append(deploy_cli)
        if deploy_cli.exit_code != 0:
            result.status = (
                DeployStatus.TIMEOUT if deploy_cli.timed_out
                else DeployStatus.DEPLOY_CMD_FAILED
            )
            result.error_message = f"wrangler exit {deploy_cli.exit_code}"
            return result

        url = _extract_url_from_output(deploy_cli.stdout_tail)
        result.deployment_url = url
        result.deployment_id = f"cfpages_{uuid.uuid4().hex[:10]}"
        result.status = DeployStatus.SUCCESS
        return result


# ---- NETLIFY ----

class NetlifyDriver(DeployDriver):
    PLATFORM = DeployPlatform.NETLIFY
    REQUIRED_CLI = ("netlify",)

    def deploy(self, request, result):
        src = Path(request.source_dir)
        if not src.exists():
            result.status = DeployStatus.ERROR
            result.error_message = f"source_dir not found: {src}"
            return result

        if request.build_cmd:
            build = _run_cli(
                shlex.split(request.build_cmd), src, request.timeout_sec,
                env=dict(request.extra_env),
            )
            result.cli_results.append(build)
            if build.exit_code != 0:
                result.status = (
                    DeployStatus.TIMEOUT if build.timed_out
                    else DeployStatus.BUILD_CMD_FAILED
                )
                result.error_message = f"build exit {build.exit_code}"
                return result

        deploy_cmd = ["netlify", "deploy", "--dir", request.output_dir]
        if request.environment == "production":
            deploy_cmd.append("--prod")

        deploy_cli = _run_cli(
            deploy_cmd, src, request.timeout_sec,
            env=dict(request.extra_env),
        )
        result.cli_results.append(deploy_cli)
        if deploy_cli.exit_code != 0:
            result.status = (
                DeployStatus.TIMEOUT if deploy_cli.timed_out
                else DeployStatus.DEPLOY_CMD_FAILED
            )
            result.error_message = f"netlify exit {deploy_cli.exit_code}"
            return result

        url = _extract_url_from_output(deploy_cli.stdout_tail)
        result.deployment_url = url
        result.deployment_id = f"netlify_{uuid.uuid4().hex[:10]}"
        result.status = DeployStatus.SUCCESS
        return result


# ---- S3 + CLOUDFRONT ----

class S3CloudFrontDriver(DeployDriver):
    PLATFORM = DeployPlatform.S3_CLOUDFRONT
    REQUIRED_CLI = ("aws",)

    def __init__(
        self,
        bucket_name: str,
        cloudfront_distribution_id: Optional[str] = None,
        aws_region: str = "us-east-1",
    ):
        self.bucket = bucket_name
        self.distribution_id = cloudfront_distribution_id
        self.region = aws_region

    def deploy(self, request, result):
        src = Path(request.source_dir)
        output = src / request.output_dir

        if request.build_cmd:
            build = _run_cli(
                shlex.split(request.build_cmd), src, request.timeout_sec,
                env=dict(request.extra_env),
            )
            result.cli_results.append(build)
            if build.exit_code != 0:
                result.status = DeployStatus.BUILD_CMD_FAILED
                result.error_message = f"build exit {build.exit_code}"
                return result

        if not output.exists():
            result.status = DeployStatus.ERROR
            result.error_message = f"output_dir not found: {output}"
            return result

        # aws s3 sync
        sync_cmd = [
            "aws", "s3", "sync", str(output), f"s3://{self.bucket}",
            "--delete", "--region", self.region,
        ]
        sync = _run_cli(sync_cmd, src, request.timeout_sec, env=dict(request.extra_env))
        result.cli_results.append(sync)
        if sync.exit_code != 0:
            result.status = DeployStatus.DEPLOY_CMD_FAILED
            result.error_message = f"s3 sync exit {sync.exit_code}"
            return result

        # CloudFront invalidation (optional)
        if self.distribution_id:
            invalidation_cmd = [
                "aws", "cloudfront", "create-invalidation",
                "--distribution-id", self.distribution_id,
                "--paths", "/*",
                "--region", self.region,
            ]
            inv = _run_cli(
                invalidation_cmd, src, request.timeout_sec,
                env=dict(request.extra_env),
            )
            result.cli_results.append(inv)
            if inv.exit_code != 0:
                result.warnings.append(
                    f"cloudfront_invalidation_failed: {inv.exit_code}"
                )

        result.deployment_id = f"s3_{uuid.uuid4().hex[:10]}"
        result.deployment_url = (
            f"https://{self.bucket}.s3.{self.region}.amazonaws.com/"
            if not self.distribution_id
            else f"https://{self.distribution_id}.cloudfront.net/"
        )
        result.status = DeployStatus.SUCCESS
        return result


# ---- GIT PUSH ----

class GitPushDriver(DeployDriver):
    PLATFORM = DeployPlatform.GIT_PUSH
    REQUIRED_CLI = ("git",)

    def __init__(self, remote: str = "origin", branch: str = "main"):
        self.remote = remote
        self.branch = branch

    def deploy(self, request, result):
        src = Path(request.source_dir)
        if not (src / ".git").exists():
            # Init repo
            init = _run_cli(["git", "init"], src, 30)
            result.cli_results.append(init)
            if init.exit_code != 0:
                result.status = DeployStatus.ERROR
                result.error_message = "git init failed"
                return result

        # Stage + commit
        add = _run_cli(["git", "add", "."], src, 60)
        result.cli_results.append(add)

        commit_msg = (
            f"APEX FACTORY v6.0 deploy {_now_iso()} - {request.notes or 'auto'}"
        )
        commit = _run_cli(
            ["git", "commit", "-m", commit_msg, "--allow-empty"],
            src, 60,
        )
        result.cli_results.append(commit)

        # Push
        push = _run_cli(
            ["git", "push", self.remote, self.branch], src, request.timeout_sec,
        )
        result.cli_results.append(push)
        if push.exit_code != 0:
            result.status = DeployStatus.DEPLOY_CMD_FAILED
            result.error_message = f"git push exit {push.exit_code}"
            return result

        # Get SHA
        sha_cli = _run_cli(["git", "rev-parse", "HEAD"], src, 10)
        sha = sha_cli.stdout_tail.strip()[:40]
        result.deployment_id = sha or f"git_{uuid.uuid4().hex[:10]}"
        result.deployment_url = f"git:{self.remote}/{self.branch}#{sha}"
        result.status = DeployStatus.SUCCESS
        return result


# ============================================================
# 5. URL EXTRACTOR
# ============================================================

def _extract_url_from_output(text: str) -> Optional[str]:
    import re
    # Tìm https URL cuối cùng trong output
    urls = re.findall(r"https?://[^\s\"']+", text)
    if not urls:
        return None
    # Ưu tiên URL có vercel.app/netlify.app/pages.dev
    for kw in ("vercel.app", "netlify.app", "pages.dev", "cloudfront.net"):
        for u in urls:
            if kw in u:
                return u.rstrip(".,;)")
    return urls[-1].rstrip(".,;)")


# ============================================================
# 6. DEPLOY LEDGER (persistent log)
# ============================================================

class DeployLedger:
    """JSONL log của mọi deploy để C2 audit + rollback."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, result: DeployResult) -> None:
        entry = result.to_dict()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        entries: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
        return entries

    def last_successful(
        self, platform: DeployPlatform, project_name: str,
    ) -> Optional[Dict[str, Any]]:
        for entry in reversed(self.read_all()):
            if (entry.get("platform") == platform.value
                    and entry.get("status") == DeployStatus.SUCCESS.value):
                return entry
        return None


# ============================================================
# 7. DEPLOY ADAPTER (main facade)
# ============================================================

PLATFORM_TO_DRIVER_CLASS: Dict[DeployPlatform, type] = {
    DeployPlatform.LOCAL_DRY_RUN: LocalDryRunDriver,
    DeployPlatform.VERCEL: VercelDriver,
    DeployPlatform.CLOUDFLARE_PAGES: CloudflarePagesDriver,
    DeployPlatform.NETLIFY: NetlifyDriver,
    # S3CloudFrontDriver + GitPushDriver cần constructor args → C2 tự inject
}


class DeployAdapter:
    """
    Facade chính. C2 chỉ cần:
        adapter = DeployAdapter(gate, kill_switch, ledger)
        result = adapter.deploy(request, token)
    """

    def __init__(
        self,
        capability_gate: CapabilityGate,
        kill_switch: KillSwitch,
        ledger: Optional[DeployLedger] = None,
        drivers: Optional[Mapping[DeployPlatform, DeployDriver]] = None,
    ):
        self.capability_gate = capability_gate
        self.kill_switch = kill_switch
        self.ledger = ledger
        self._drivers: Dict[DeployPlatform, DeployDriver] = dict(drivers or {})

    def register_driver(
        self, platform: DeployPlatform, driver: DeployDriver,
    ) -> None:
        self._drivers[platform] = driver

    def _driver_for(self, platform: DeployPlatform) -> DeployDriver:
        if platform in self._drivers:
            return self._drivers[platform]
        driver_class = PLATFORM_TO_DRIVER_CLASS.get(platform)
        if driver_class is None:
            raise ValueError(
                f"No driver for platform {platform.value}. "
                f"Register via register_driver()."
            )
        driver = driver_class()
        self._drivers[platform] = driver
        return driver

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def deploy(
        self,
        request: DeployRequest,
        token: CapabilityToken,
    ) -> DeployResult:
        t0 = time.perf_counter()
        result = DeployResult(
            request_id=request.request_id,
            platform=request.platform,
            status=DeployStatus.SUCCESS,   # tentative
        )

        # 0. Kill switch
        if self.kill_switch.is_activated():
            result.status = DeployStatus.KILL_SWITCH
            result.error_message = "kill_switch_active"
            return self._finalize(result, t0)

        # 1. Authorize token
        try:
            self.capability_gate.authorize(
                token=token,
                required_scope=DEPLOY_TOKEN_SCOPE,
                required_resource=(
                    f"deploy:{request.platform.value}:{request.project_name}"
                ),
            )
            result.c2_token_id = token.token_id
        except Exception as e:
            result.status = DeployStatus.AUTH_DENIED
            result.error_message = f"token_rejected: {e}"
            return self._finalize(result, t0)

        # 2. Driver available?
        try:
            driver = self._driver_for(request.platform)
        except ValueError as e:
            result.status = DeployStatus.ERROR
            result.error_message = str(e)
            return self._finalize(result, t0)

        if not driver.is_available():
            result.status = DeployStatus.CLI_MISSING
            result.error_message = (
                f"Required CLI(s) missing: {driver.REQUIRED_CLI}. "
                f"Install trước khi deploy."
            )
            return self._finalize(result, t0)

        # 3. Track previous deployment cho rollback
        if self.ledger:
            prev = self.ledger.last_successful(request.platform, request.project_name)
            if prev:
                result.previous_deployment_id = prev.get("deployment_id")

        # 4. Driver deploy
        try:
            result = driver.deploy(request, result)
        except Exception as e:
            result.status = DeployStatus.ERROR
            result.error_message = f"driver_exception: {type(e).__name__}: {e}"

        return self._finalize(result, t0)

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def deploy_build_artifact(
        self,
        artifact: BuildArtifact,
        request_template: DeployRequest,
        token: CapabilityToken,
    ) -> DeployResult:
        """
        Convenience: ghi BuildArtifact.emit_result xuống source_dir rồi deploy.
        """
        if artifact.emit_result is None:
            return DeployResult(
                request_id=request_template.request_id,
                platform=request_template.platform,
                status=DeployStatus.ERROR,
                error_message="BuildArtifact.emit_result is None",
            )
        Path(request_template.source_dir).mkdir(parents=True, exist_ok=True)
        artifact.emit_result.write_to_disk(request_template.source_dir)
        return self.deploy(request_template, token)

    def _finalize(self, result: DeployResult, t0: float) -> DeployResult:
        result.elapsed_sec = time.perf_counter() - t0
        result.finished_at_utc = _now_iso()
        if self.ledger:
            try:
                self.ledger.append(result)
            except Exception:
                pass
        return result

    # ---- Rollback ----

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def rollback_to_previous(
        self,
        platform: DeployPlatform,
        project_name: str,
        token: CapabilityToken,
    ) -> DeployResult:
        """
        Tìm deployment success TRƯỚC deployment hiện tại và re-deploy nó
        (platform-specific, hiện tại skeleton - mỗi driver nên override).
        """
        if self.ledger is None:
            return DeployResult(
                request_id=f"rollback_{uuid.uuid4().hex[:8]}",
                platform=platform,
                status=DeployStatus.ERROR,
                error_message="ledger_not_configured",
            )

        # Lấy 2 deploy success gần nhất - thứ 2 (trước thứ 1)
        all_entries = [
            e for e in self.ledger.read_all()
            if (e.get("platform") == platform.value
                and e.get("status") == DeployStatus.SUCCESS.value)
        ]
        if len(all_entries) < 2:
            return DeployResult(
                request_id=f"rollback_{uuid.uuid4().hex[:8]}",
                platform=platform,
                status=DeployStatus.ERROR,
                error_message="no_previous_deploy_to_rollback_to",
            )
        target = all_entries[-2]     # deploy thứ 2 từ cuối = trước cái hiện tại
        result = DeployResult(
            request_id=f"rollback_{uuid.uuid4().hex[:8]}",
            platform=platform,
            status=DeployStatus.SUCCESS,
            deployment_id=target.get("deployment_id"),
            deployment_url=target.get("deployment_url"),
            previous_deployment_id=all_entries[-1].get("deployment_id"),
            warnings=[
                f"Rollback to {target.get('deployment_id')} - "
                f"platform-specific re-deploy required manually. "
                f"This is a ledger marker only."
            ],
            c2_token_id=token.token_id,
        )
        # Verify token
        try:
            self.capability_gate.authorize(
                token=token,
                required_scope=DEPLOY_TOKEN_SCOPE,
                required_resource=f"rollback:{platform.value}:{project_name}",
            )
        except Exception as e:
            result.status = DeployStatus.AUTH_DENIED
            result.error_message = f"token_rejected: {e}"

        if self.ledger:
            try:
                self.ledger.append(result)
            except Exception:
                pass
        return result


# ============================================================
# 8. SANITY CHECK
# ============================================================

def deploy_adapter_sanity_check(tmp_path: Optional[Path] = None) -> Dict[str, bool]:
    import tempfile
    checks: Dict[str, bool] = {}
    tmp = tmp_path or Path(tempfile.mkdtemp(prefix="deploy_test_"))

    # Setup capability gate
    if not os.environ.get("C2_MASTER_SECRET"):
        os.environ["C2_MASTER_SECRET"] = "test" * 16
    from apex_core.legacy.foundation.capability_token import (
        CapabilityTokenSigner,
        NonceStore,
    )
    signer = CapabilityTokenSigner()
    nonce_store = NonceStore(tmp / "nonces.json")
    gate = CapabilityGate(signer, nonce_store)
    kill_switch = KillSwitch(tmp / "kill.flag")
    ledger = DeployLedger(tmp / "deploy_log.jsonl")

    adapter = DeployAdapter(gate, kill_switch, ledger)

    # Test 1: dry run success
    source_dir = tmp / "project"
    source_dir.mkdir()
    (source_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    token = signer.sign(
        scope=DEPLOY_TOKEN_SCOPE,
        target_resource="deploy:local_dry_run:test-app",
        ttl_seconds=600,
    )
    req = DeployRequest(
        request_id="req_001",
        platform=DeployPlatform.LOCAL_DRY_RUN,
        source_dir=str(source_dir),
        project_name="test-app",
    )
    result = adapter.deploy(req, token)
    checks["dry_run_success"] = result.status == DeployStatus.SUCCESS
    checks["ledger_logged"] = len(ledger.read_all()) >= 1

    # Test 2: kill switch blocks
    kill_switch.activate("test")
    token2 = signer.sign(
        scope=DEPLOY_TOKEN_SCOPE,
        target_resource="deploy:local_dry_run:test-app",
        ttl_seconds=600,
    )
    req2 = DeployRequest(
        request_id="req_002",
        platform=DeployPlatform.LOCAL_DRY_RUN,
        source_dir=str(source_dir),
        project_name="test-app",
    )
    result2 = adapter.deploy(req2, token2)
    checks["kill_switch_blocks"] = result2.status == DeployStatus.KILL_SWITCH
    kill_switch.deactivate()

    # Test 3: wrong scope rejected
    bad_token = signer.sign(
        scope="hot_inject",    # sai scope
        target_resource="deploy:local_dry_run:test-app",
        ttl_seconds=600,
    )
    req3 = DeployRequest(
        request_id="req_003",
        platform=DeployPlatform.LOCAL_DRY_RUN,
        source_dir=str(source_dir),
        project_name="test-app",
    )
    result3 = adapter.deploy(req3, bad_token)
    checks["wrong_scope_rejected"] = result3.status == DeployStatus.AUTH_DENIED

    # Test 4: CLI missing khi dùng platform thật (nếu máy không có vercel CLI)
    token4 = signer.sign(
        scope=DEPLOY_TOKEN_SCOPE,
        target_resource="deploy:vercel:test-app",
        ttl_seconds=600,
    )
    req4 = DeployRequest(
        request_id="req_004",
        platform=DeployPlatform.VERCEL,
        source_dir=str(source_dir),
        project_name="test-app",
    )
    result4 = adapter.deploy(req4, token4)
    # Có thể SUCCESS nếu máy C2 có cài vercel, có thể CLI_MISSING
    checks["vercel_responds_cleanly"] = result4.status in (
        DeployStatus.CLI_MISSING, DeployStatus.DEPLOY_CMD_FAILED,
        DeployStatus.SUCCESS, DeployStatus.ERROR, DeployStatus.BUILD_CMD_FAILED,
    )

    # Test 5: Result serializable
    try:
        json.dumps(result.to_dict(), default=str)
        checks["result_serializable"] = True
    except Exception:
        checks["result_serializable"] = False

    # Test 6: URL extractor
    sample_output = (
        "Deployed!\n"
        "Production: https://my-app-abc123.vercel.app [ready]\n"
    )
    url = _extract_url_from_output(sample_output)
    checks["url_extractor_works"] = url == "https://my-app-abc123.vercel.app"

    return checks


__all__ = [
    "DEPLOY_ADAPTER_VERSION", "DEPLOY_TOKEN_SCOPE",
    "DeployPlatform", "DeployStatus",
    "DeployRequest", "DeployResult", "CliResult",
    "DeployDriver",
    "LocalDryRunDriver", "VercelDriver", "CloudflarePagesDriver",
    "NetlifyDriver", "S3CloudFrontDriver", "GitPushDriver",
    "PLATFORM_TO_DRIVER_CLASS",
    "DeployLedger", "DeployAdapter",
    "deploy_adapter_sanity_check",
]

