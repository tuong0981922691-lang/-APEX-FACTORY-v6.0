# AGENTS.md

## Cursor Cloud specific instructions

### Project Overview

APEX Factory v6.0 is a multi-platform production factory that generates web apps, mobile apps, videos, and images from natural language briefs. The codebase is pure Python (stdlib-only core) with optional LLM/server/image dependencies.

### Services

| Service | Command | Notes |
|---------|---------|-------|
| CLI (main entry) | `python3 -m apex_core.orchestrator_v6.studio_entry --cmd <command>` | Single-shot commands: `status`, `help`, `build <brief>`, `version` |
| Interactive REPL | `python3 -m apex_core.orchestrator_v6.studio_entry` | Interactive console |
| FastAPI server | `python3 -m apex_core.orchestrator_v6.studio_entry --serve` | Requires `pip install fastapi uvicorn` |

### Key Commands

- **Lint:** `ruff check apex_core/ tests/`
- **Tests:** `pytest tests/ -v`
- **Run app:** `python3 -m apex_core.orchestrator_v6.studio_entry --cmd status`
- **Build project:** `python3 -m apex_core.orchestrator_v6.studio_entry --cmd "build <brief>"`

### Important Notes

- Use `python3` not `python` (the VM does not have `python` symlink).
- The system runs in READ-ONLY mode without `C2_MASTER_SECRET` env var. Set it for write operations: `export C2_MASTER_SECRET="your-secret"`.
- Node.js 20 is required for emitters/preview sandbox (generates React/Vue/Remotion projects).
- All LLM providers (OpenAI, Anthropic, Google) are optional lazy imports - the system runs fine without them using a mock adapter.
- The legacy module (`apex_core/legacy/`) provides v5.0 compatibility stubs (capability tokens, principles, brain base). These are reconstructed from the blueprint spec.
- E701 lint rule (multiple-statements-on-one-line) is intentionally ignored in `pyproject.toml` as it's the codebase's style.
