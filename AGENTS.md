# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

**botthongminh.com** — AI app shop (website builder, mobile app, algorithm store) with C2 Command Room.
Stack: **Python 3.12 + FastAPI + uvicorn + SQLite + HTML/CSS/JS** (NO Next.js, NO npm).

### Key commands (all from repo root `/workspace`)

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` |
| Dev server | `python -m apex_core.orchestrator_v6.studio_entry --serve --host 0.0.0.0 --port 8787` |
| Run tests | `pytest tests/ -v` |
| Lint | `ruff check .` |
| Lint fix | `ruff check --fix .` |
| Format | `ruff format .` |

### Architecture

- `apex_core/orchestrator_v6/studio_entry.py` — FastAPI app factory (entry point)
- `apex_core/orchestrator_v6/_hookup.py` — Extension loader (includes new routers)
- `apex_core/orchestrator_v6/c2_hub_router.py` — 8-module C2 Hub API
- `apex_core/orchestrator_v6/orders_router.py` — Order flow + CDP dialogue
- `apex_core/orchestrator_v6/twofa_router.py` — TOTP 2FA
- `apex_core/orchestrator_v6/recovery_router.py` — Recovery flow
- `apex_core/auth/` — Existing auth (user_store, session_store, router)
- `apex_core/db/botthongminh_schema.py` — SQLite schema (5 tables)
- `public_site/` — Static HTML mounted at `/site/`
- `public_site/command-room/` — C2 dashboard pages
- `public_site/orders/` — Customer order pages

### Dev environment notes

- **Python 3.12** with venv at `./venv/`.
- **SQLite** database auto-created at `storage/botthongminh.db` on first request.
- Static files served at `/site/` via FastAPI `StaticFiles` mount.
- API docs available at `http://localhost:8787/docs` (Swagger UI).
- The dev server uses `--reload` mode by default — file changes trigger automatic restart.
- **Do NOT modify** existing files in `apex_core/auth/` or `public_site/portal.html` — extend only.
- Environment variables: copy `.env.example` to `.env` for secrets (Telegram, Gmail, etc.).

### Gotchas

- The `storage/` directory is gitignored — it contains runtime SQLite DB and session data.
- `chromadb` is a heavy dependency (installed but not actively used in v1 order flow).
- When running tests, each test creates its own `storage/botthongminh.db` — clean between full test runs if needed.
- The `_hookup.py` is loaded at import time from `studio_entry.py` — if new routers have import errors, the entire app fails to start.
