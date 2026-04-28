"""Command-line entrypoint for the runnable APEX Factory scaffold."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from apex_core.orchestrator_v6.apex_factory import (
    APEX_FACTORY_VERSION,
    BANNER,
    ApexFactory,
    ApexFactoryConfig,
)


def _build_default_factory(storage_dir: str | None = None) -> ApexFactory:
    config = ApexFactoryConfig(storage_dir=Path(storage_dir or "./apex_factory_storage"))
    return ApexFactory(config=config)


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def run_command(factory: ApexFactory, command: str) -> int:
    command = command.strip()
    if command in {"status", "health"}:
        _print_json(factory.get_health_snapshot())
        return 0
    if command in {"version", "--version"}:
        _print_json({"version": APEX_FACTORY_VERSION})
        return 0
    if command == "boot":
        _print_json(factory.boot())
        return 0
    if command.startswith("build "):
        _print_json(factory.build_web_project(command.removeprefix("build ").strip()))
        return 0
    if command == "help":
        _print_json({"commands": ["status", "boot", "version", "build <brief>"]})
        return 0
    _print_json({"error": f"Unknown command: {command}", "commands": ["status", "boot", "version", "build <brief>"]})
    return 2


def serve(factory: ApexFactory, port: int) -> int:
    try:
        from fastapi import FastAPI
        import uvicorn
    except ImportError:
        _print_json({"error": "Install optional dependencies with `pip install -e .[serve]` to run the HTTP API."})
        return 1

    app = FastAPI(title="APEX Factory v6", version=APEX_FACTORY_VERSION)

    @app.get("/health")
    def health() -> dict[str, Any]:
        return factory.get_health_snapshot()

    uvicorn.run(app, host="127.0.0.1", port=port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=BANNER)
    parser.add_argument("--cmd", help="Run a one-shot studio command")
    parser.add_argument("--serve", action="store_true", help="Run the optional HTTP API")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--storage-dir", default=None)
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args(argv)

    factory = _build_default_factory(args.storage_dir)
    if args.version:
        return run_command(factory, "version")
    if args.serve:
        return serve(factory, args.port)
    if args.cmd:
        return run_command(factory, args.cmd)

    print(BANNER)
    print("Use --cmd status, --cmd boot, --cmd version, or --cmd 'build <brief>'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main", "run_command", "serve", "_build_default_factory"]
