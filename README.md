# -APEX-FACTORY-v6.0
# ⚖️ THIẾT QUÂN LUẬT VẬN HÀNH APEX FACTORY v6.0 **TRẠNG THÁI:** TỐI MẬT - BẮT BUỘC TUÂN THỦ 100%

## Development quick start

This repository now includes a runnable Python scaffold for the APEX Factory v6
orchestrator described in `ARCHITECTURAL_BLUEPRINT_V6.md`.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[test]
python3 -m apex_core.orchestrator_v6.studio_entry --cmd status
pytest
```

Optional HTTP API support is available with:

```bash
pip install -e .[serve]
python3 -m apex_core.orchestrator_v6.studio_entry --serve --port 8787
```
