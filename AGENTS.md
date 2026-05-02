# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

**botthongminh.com** — AI app shop (website builder, mobile app, algorithm store) with C2 Command Room. Runs on VPS Ubuntu 22.04 at IP 14.225.224.168.

Stack: **Python 3.12 + FastAPI + uvicorn + SQLite + HTML/CSS/JS** (NO Next.js, NO npm, NO Supabase).

The blueprint specifies EXTEND-only: do not rewrite existing files, only add new modules and include them via `app.include_router(...)`.

### Key commands (all from repo root `/workspace`)

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` |
| Dev server | `python -m apex_core.orchestrator_v6.studio_entry --serve --host 0.0.0.0 --port 8787` |
| Run tests | `pytest tests/ -v` |
| Lint | `ruff check .` |
| Lint fix | `ruff check --fix .` |
| Format | `ruff format .` |
| NT26 lint | `python scripts/lint_no_self_reference.py` |

### Architecture

```
apex_core/
├── orchestrator_v6/studio_entry.py    ← FastAPI app factory (entry point)
├── orchestrator_v6/_hookup.py         ← Extension loader
├── orchestrator_v6/c2_hub_router.py   ← 8-module C2 Hub API
├── orchestrator_v6/orders_router.py   ← Order flow + CDP dialogue
├── orchestrator_v6/twofa_router.py    ← TOTP 2FA
├── orchestrator_v6/recovery_router.py ← Recovery flow
├── routers/botthongminh_router.py     ← Aggregated router (/api/v1/*)
├── auth/                              ← Existing auth (user_store, session_store)
├── customer/                          ← CDP, CVP, Saint Protocol
├── governance/                        ← Round Table, Decision Brain
├── probes/                            ← Reverse-code, silence, cross-AI probes
├── subagent/                          ← Student 3-tier subagent
├── db/botthongminh_schema.py          ← SQLite schema (5 tables)
└── c2/                                ← C2 login, order inbox, brain status

public_site/                           ← Static HTML mounted at /site/
├── portal.html                        ← Main portal (8 cards)
├── customer-chat.html                 ← CDP UI
├── command-room/                      ← C2 dashboard pages
├── orders/                            ← Customer order pages
├── c2/login.html                      ← 3-layer auth login
└── static/css/saint.css               ← "Khách là Thánh" UI rules
```

### Dev environment notes

- **Python 3.12** with venv at `./venv/`.
- **SQLite** database auto-created at `storage/botthongminh.db` on first request.
- Static files served at `/site/` via FastAPI `StaticFiles` mount.
- API docs: `http://localhost:8787/docs` (Swagger UI).
- Dev server uses `--reload` mode — file changes trigger automatic restart.
- The `data/` directory stores runtime data (orders, radar, round_table, audit_log).
- The `reports/` directory stores construction logs and evidence.

### Key rules (from blueprint)

- **EXTEND only**: do not modify existing files except the 1-line include in `_hookup.py`.
- **No mock**: Telegram, Gmail, OTP must be real when deployed.
- **NT26**: No model name self-references in code/reports (enforced by `scripts/lint_no_self_reference.py`).
- **NT21 Ốc vít**: Stop and log in `reports/SCREW_LOG.md` when encountering warnings.
- Environment variables: copy `.env.example` to `.env` for secrets.

### Gotchas

- The `storage/` and `data/` directories are gitignored — runtime data only.
- `chromadb` is listed in requirements but not actively used in v1 order flow.
- The `_hookup.py` is loaded at import time — import errors in new routers crash the entire app.
- Tests create their own SQLite DB; clean `storage/` between full test runs if needed.
- The NT26 lint script (`scripts/lint_no_self_reference.py`) scans `apex_core/`, `public_site/`, and `tests/` — not `scripts/` itself (since it contains the regex pattern).
