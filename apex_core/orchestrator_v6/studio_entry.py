"""
APEX FACTORY v6.0 - Orchestrator Layer (v6)
File: studio_entry.py

Mục đích: Entry point chính cho C2.
    - CLI argparse (chạy 1-shot command)
    - Interactive REPL (C2 console)
    - Optional FastAPI Web UI (nếu fastapi install)
    - Banner + help tiếng Việt

Sử dụng:
    python -m apex_core.orchestrator_v6.studio_entry              # interactive
    python -m apex_core.orchestrator_v6.studio_entry --cmd status # single command
    python -m apex_core.orchestrator_v6.studio_entry --serve      # FastAPI server
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from apex_core.foundation.ontology_ui import ComponentCatalog, TokenRegistry
from apex_core.orchestrator_v6.apex_factory import (
    APEX_FACTORY_VERSION,
    BANNER,
    ApexFactory,
    ApexFactoryConfig,
)

# ============================================================
# 0. VERSION
# ============================================================

STUDIO_ENTRY_VERSION = "6.0.0"


# ============================================================
# 1. COMMAND REGISTRY
# ============================================================

@dataclass
class StudioCommand:
    name: str
    description_vi: str
    handler: Callable
    required_args: List[str] = None
    requires_capability: bool = False

    def __post_init__(self):
        if self.required_args is None:
            self.required_args = []


class StudioConsole:
    """Console REPL với registry lệnh."""

    def __init__(self, factory: ApexFactory):
        self.factory = factory
        self.commands: Dict[str, StudioCommand] = {}
        self.history: List[Dict[str, Any]] = []
        self._register_builtin()

    # ---- Builtin commands ----

    def _register_builtin(self) -> None:
        self.register(StudioCommand(
            name="help",
            description_vi="Hiển thị danh sách lệnh",
            handler=self._cmd_help,
        ))
        self.register(StudioCommand(
            name="status",
            description_vi="Xem trạng thái toàn hệ thống",
            handler=self._cmd_status,
        ))
        self.register(StudioCommand(
            name="boot",
            description_vi="Chạy lại boot + self-check",
            handler=self._cmd_boot,
        ))
        self.register(StudioCommand(
            name="build",
            description_vi="Build web project từ brief",
            handler=self._cmd_build,
            required_args=["brief"],
        ))
        self.register(StudioCommand(
            name="catalog",
            description_vi="Xem component catalog",
            handler=self._cmd_catalog,
        ))
        self.register(StudioCommand(
            name="tokens",
            description_vi="Xem token registry",
            handler=self._cmd_tokens,
        ))
        self.register(StudioCommand(
            name="llm",
            description_vi="Liệt kê LLM adapters + cost tracking",
            handler=self._cmd_llm,
        ))
        self.register(StudioCommand(
            name="errors",
            description_vi="Top error clusters cần vá",
            handler=self._cmd_errors,
        ))
        self.register(StudioCommand(
            name="kill",
            description_vi="Kill switch ON/OFF",
            handler=self._cmd_kill,
            required_args=["action"],
            requires_capability=True,
        ))
        self.register(StudioCommand(
            name="token",
            description_vi="Ký Capability Token",
            handler=self._cmd_token,
            required_args=["scope", "resource"],
            requires_capability=True,
        ))
        self.register(StudioCommand(
            name="export",
            description_vi="Export full state ra JSON file",
            handler=self._cmd_export,
            required_args=["path"],
        ))
        self.register(StudioCommand(
            name="version",
            description_vi="Version info",
            handler=self._cmd_version,
        ))

    def register(self, cmd: StudioCommand) -> None:
        self.commands[cmd.name] = cmd

    # ---- Execute ----

    def execute(self, raw_input: str) -> Dict[str, Any]:
        tokens = raw_input.strip().split(maxsplit=1)
        if not tokens:
            return {"success": False, "message": "Lệnh rỗng"}

        cmd_name = tokens[0].lower()
        rest_args = tokens[1] if len(tokens) > 1 else ""

        cmd = self.commands.get(cmd_name)
        if cmd is None:
            return {
                "success": False,
                "message": f"Không biết lệnh '{cmd_name}'. Gõ 'help'.",
            }

        try:
            result = cmd.handler(rest_args)
            self.history.append({
                "cmd": cmd_name, "args": rest_args, "success": True,
            })
            return {"success": True, "result": result}
        except Exception as e:
            self.history.append({
                "cmd": cmd_name, "args": rest_args,
                "success": False, "error": str(e),
            })
            return {
                "success": False,
                "message": f"Lỗi {type(e).__name__}: {e}",
            }

    # ---- Handlers ----

    def _cmd_help(self, args: str) -> Dict[str, Any]:
        lines = ["", f"🏭 APEX FACTORY v{APEX_FACTORY_VERSION} — Lệnh CLI:"]
        for name in sorted(self.commands.keys()):
            cmd = self.commands[name]
            gate = "🔐 " if cmd.requires_capability else "   "
            args_str = " ".join(f"<{a}>" for a in cmd.required_args)
            lines.append(f"  {gate}{name:12} {args_str:30} → {cmd.description_vi}")
        lines.append("")
        lines.append("🔐 = cần Capability Token (set C2_MASTER_SECRET)")
        return {"help_text": "\n".join(lines)}

    def _cmd_status(self, args: str) -> Dict[str, Any]:
        snap = self.factory.get_health_snapshot()
        return {
            "summary": (
                f"🟢 v{snap['version']} ({snap['codename']})\n"
                f"   project_id: {snap['project_id']}\n"
                f"   booted: {snap['booted']}\n"
                f"   kill_switch: {'🛑 ACTIVE' if snap['kill_switch_active'] else '✅ OFF'}\n"
                f"   capability_signer: {'✅' if snap['capability_signer_ready'] else '❌ (set C2_MASTER_SECRET)'}\n"
                f"   catalog: {snap['catalog']['size']} components (fp: {snap['catalog']['fingerprint']})\n"
                f"   tokens: {sum(snap['token_registry'].get(k, 0) for k in ('colors','spacing','radius','shadow','motion','icons','typography'))} tokens\n"
                f"   lineage: {snap['lineage']['total_snapshots']} snapshots\n"
                f"   errors logged: {snap['error_ledger']['total_entries']}"
            ),
            "raw": snap,
        }

    def _cmd_boot(self, args: str) -> Dict[str, Any]:
        report = self.factory.boot()
        return report

    def _cmd_build(self, args: str) -> Dict[str, Any]:
        if not args.strip():
            raise ValueError("Cú pháp: build <brief text>")
        artifact = self.factory.build_web(args.strip())
        return {
            "build_id": artifact.build_id,
            "status": artifact.status.value,
            "best_variant_id": artifact.best_variant_id,
            "variant_count": len(artifact.variants_evaluated),
            "fix_proposals_count": len(artifact.fix_proposals),
            "elapsed_sec": round(artifact.elapsed_sec, 2),
            "warnings": artifact.warnings[:5],
            "errors": artifact.errors[:5],
        }

    def _cmd_catalog(self, args: str) -> Dict[str, Any]:
        items = self.factory.catalog.all()
        return {
            "size": len(items),
            "by_category": {
                cat: len(self.factory.catalog.search_by_category(cat))
                for cat in {spec.category for spec in items}
            } if items else {},
            "sample_ids": [s.component_id for s in items[:10]],
            "fingerprint": self.factory.catalog.fingerprint()[:16],
        }

    def _cmd_tokens(self, args: str) -> Dict[str, Any]:
        return {
            "summary": self.factory.registry.summary(),
            "fingerprint": self.factory.registry.fingerprint()[:16],
        }

    def _cmd_llm(self, args: str) -> Dict[str, Any]:
        if self.factory._llm_broker is None:
            return {"enabled": False, "message": "LLM broker not initialized"}
        return self.factory._llm_broker.summary()

    def _cmd_errors(self, args: str) -> Dict[str, Any]:
        top = self.factory.error_ledger.top_fix_candidates(top_k=10)
        return {
            "top_clusters": [c.to_dict() for c in top],
            "summary": self.factory.error_ledger.summary(),
        }

    def _cmd_kill(self, args: str) -> Dict[str, Any]:
        parts = args.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "status"
        reason = parts[1] if len(parts) > 1 else "C2 CLI"

        if action in ("on", "activate", "1", "true"):
            return self.factory.c2_kill_switch(True, reason)
        elif action in ("off", "deactivate", "0", "false"):
            return self.factory.c2_kill_switch(False)
        elif action == "status":
            return {"active": self.factory.kill_switch.is_activated()}
        else:
            raise ValueError("Cú pháp: kill on|off|status [reason]")

    def _cmd_token(self, args: str) -> Dict[str, Any]:
        parts = args.strip().split(maxsplit=2)
        if len(parts) < 2:
            raise ValueError("Cú pháp: token <scope> <resource> [ttl_seconds]")
        scope = parts[0]
        resource = parts[1]
        ttl = int(parts[2]) if len(parts) > 2 else 3600

        tok = self.factory.c2_issue_token(
            scope=scope, target_resource=resource, ttl_seconds=ttl,
        )
        if tok is None:
            return {
                "success": False,
                "error": "Signer not initialized (set C2_MASTER_SECRET)",
            }
        return {
            "success": True,
            "token_id": tok.token_id,
            "scope": tok.scope,
            "target_resource": tok.target_resource,
            "expires_at_utc": tok.expires_at_utc,
            "signature_preview": tok.signature_hmac_sha256[:16] + "...",
            "note": (
                "Token printed - lưu vào biến env/secret. "
                "Mỗi token chỉ dùng 1 lần (nonce protection)."
            ),
        }

    def _cmd_export(self, args: str) -> Dict[str, Any]:
        path = Path(args.strip())
        result = self.factory.export_state(path)
        return {"exported_to": str(result), "size_bytes": result.stat().st_size}

    def _cmd_version(self, args: str) -> Dict[str, Any]:
        return {
            "apex_factory": APEX_FACTORY_VERSION,
            "studio_entry": STUDIO_ENTRY_VERSION,
            "python": sys.version.split()[0],
            "platform": sys.platform,
        }


# ============================================================
# 2. INTERACTIVE LOOP
# ============================================================

def run_interactive(factory: ApexFactory) -> None:
    console = StudioConsole(factory)

    print("=" * 64)
    print(BANNER)
    print("=" * 64)
    print()
    print(f" Project ID: {factory.project_id}")
    print(f" Storage:    {factory.config.storage_root}")
    print(f" Booted:     {factory._booted}")
    if factory._init_signer_error:
        print(f" ⚠️  {factory._init_signer_error}")
    print()
    print(" Gõ 'help' để xem lệnh, 'exit' để thoát.")
    print()

    while True:
        try:
            raw = input("APEX > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye C2!")
            return
        if not raw:
            continue
        if raw.lower() in ("exit", "quit", "q"):
            print("👋 Goodbye C2!")
            return

        result = console.execute(raw)
        _print_result(result)
        print()


def _print_result(result: Dict[str, Any]) -> None:
    if result.get("success"):
        r = result.get("result", {})
        if isinstance(r, dict) and "help_text" in r:
            print(r["help_text"])
        elif isinstance(r, dict) and "summary" in r:
            print(r["summary"])
            if "raw" in r:
                print()
                print("--- raw ---")
                print(json.dumps(r["raw"], indent=2, ensure_ascii=False, default=str)[:2000])
        else:
            print(json.dumps(r, indent=2, ensure_ascii=False, default=str)[:3000])
    else:
        print(f"❌ {result.get('message', 'Unknown error')}")


# ============================================================
# 3. FASTAPI SERVER (optional)
# ============================================================

def try_run_fastapi(factory: ApexFactory, host: str, port: int) -> int:
    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
    except ImportError:
        print(
            "❌ FastAPI/uvicorn chưa install. "
            "Cài: pip install fastapi uvicorn[standard]"
        )
        return 1

    app = FastAPI(
        title="APEX Factory Studio API",
        version=APEX_FACTORY_VERSION,
        description="HTTP facade cho ApexFactory - C2 Studio backend",
    )
    console = StudioConsole(factory)

    @app.get("/")
    def root():
        return {
            "name": "APEX Factory",
            "version": APEX_FACTORY_VERSION,
            "booted": factory._booted,
        }

    @app.get("/health")
    def health():
        return factory.get_health_snapshot()

    @app.post("/command")
    def run_command(payload: Dict[str, Any]):
        cmd = payload.get("cmd", "")
        if not cmd:
            raise HTTPException(400, "field 'cmd' required")
        result = console.execute(cmd)
        status_code = 200 if result.get("success") else 400
        return JSONResponse(content=result, status_code=status_code)

    @app.post("/build/web")
    def build_web(payload: Dict[str, Any]):
        brief = payload.get("brief", "")
        if not brief.strip():
            raise HTTPException(400, "field 'brief' required")
        artifact = factory.build_web(brief, c2_signal=payload.get("c2_signal"))
        return artifact.to_dict()

    @app.post("/kill-switch/{action}")
    def kill_switch(action: str, payload: Optional[Dict[str, Any]] = None):
        reason = (payload or {}).get("reason", "API")
        if action == "on":
            return factory.c2_kill_switch(True, reason)
        if action == "off":
            return factory.c2_kill_switch(False)
        raise HTTPException(400, "action must be 'on' or 'off'")

    print(f"🚀 APEX Factory Studio API running at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


# ============================================================
# 4. MAIN
# ============================================================

def _build_default_factory(storage_root: Path) -> ApexFactory:
    """Factory với catalog + registry rỗng (C2 tự seed khi dùng thật)."""
    from apex_core.foundation.ontology_ui import ColorToken, TokenRole
    catalog = ComponentCatalog()
    registry = TokenRegistry()
    # Seed 1 color để registry không rỗng
    registry.add(ColorToken(
        token_id="brand.primary", value="#2563EB", role=TokenRole.PRIMARY,
    ))
    registry.freeze()
    return ApexFactory(
        component_catalog=catalog,
        token_registry=registry,
        config=ApexFactoryConfig(storage_root=storage_root),
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apex-factory",
        description="APEX FACTORY v6.0 - Omni-Domain Production System",
    )
    parser.add_argument(
        "--storage", type=Path, default=Path("./apex_factory_storage"),
        help="Root directory cho storage (default: ./apex_factory_storage)",
    )
    parser.add_argument(
        "--cmd", type=str, default=None,
        help="Chạy 1 command rồi exit (VD: --cmd status)",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Chạy FastAPI server",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="FastAPI host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=8787,
        help="FastAPI port (default: 8787)",
    )
    parser.add_argument(
        "--version", action="store_true",
        help="In version rồi thoát",
    )

    args = parser.parse_args(argv)

    if args.version:
        print(f"APEX FACTORY v{APEX_FACTORY_VERSION}")
        print(f"Studio Entry v{STUDIO_ENTRY_VERSION}")
        return 0

    if not os.environ.get("C2_MASTER_SECRET"):
        print(
            "⚠️  WARNING: C2_MASTER_SECRET chưa set.\n"
            "   Hệ thống READ-ONLY (không ký Capability Token được).\n"
            "   Set:  export C2_MASTER_SECRET='your-64-char-secret-here...'\n"
        )

    factory = _build_default_factory(args.storage)

    if args.serve:
        return try_run_fastapi(factory, args.host, args.port)

    if args.cmd:
        console = StudioConsole(factory)
        result = console.execute(args.cmd)
        _print_result(result)
        return 0 if result.get("success") else 1

    # Default: interactive
    run_interactive(factory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
