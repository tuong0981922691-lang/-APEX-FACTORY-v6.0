# Workspace cleared

This repository working tree was wiped on purpose to start a **new project** with a clean checkout.

- No virtual environment, no build artifacts, no runtime storage paths are present in this tree.
- Clone or add your new source here, then create a branch and begin work as usual.

To remove Python caches and local venv later (on your machine):

```bash
rm -rf .venv venv __pycache__ .pytest_cache .ruff_cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```
