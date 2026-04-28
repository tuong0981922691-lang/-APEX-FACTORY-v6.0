# -APEX-FACTORY-v6.0
# ⚖️ THIẾT QUÂN LUẬT VẬN HÀNH APEX FACTORY v6.0 **TRẠNG THÁI:** TỐI MẬT - BẮT BUỘC TUÂN THỦ 100%

## Auto setup

Run the repository bootstrap on Linux/macOS:

```bash
bash scripts/auto_setup.sh
```

The script creates a local virtual environment, installs `requirements.txt`, and
runs a project status check. If the implementation source tree (`apex_core`,
`tests`, `scripts` beyond setup helpers) is missing, the status check reports it
clearly so the full source package can be synced before continuing sprint work.

To inspect status without installing dependencies:

```bash
python3 scripts/project_status.py
```
