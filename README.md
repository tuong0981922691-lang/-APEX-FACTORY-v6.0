# botthongminh.com — APEX core (FastAPI)

**APEX FACTORY v6.0** — operational rules: see constitution / blueprint in project docs as needed.

This repository contains the **botthongminh.com** backend (`apex_core/`), static site (`public_site/`), and tests. For Cursor agents and day-to-day commands, start with:

**[AGENTS.md](AGENTS.md)**

Quick start:

```bash
cp .env.example .env   # then edit secrets
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m apex_core.orchestrator_v6.studio_entry --serve --host 0.0.0.0 --port 8787
```
