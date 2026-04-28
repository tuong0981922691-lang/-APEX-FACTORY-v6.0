#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
  printf '[auto-setup] %s\n' "$*"
}

warn() {
  printf '[auto-setup][WARN] %s\n' "$*" >&2
}

fail() {
  printf '[auto-setup][ERROR] %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

check_project_sources() {
  local missing=0

  if [[ ! -d "$ROOT_DIR/apex_core" ]]; then
    warn "Missing apex_core/. The current checkout contains documents/blueprints, not the full runnable source tree."
    missing=1
  fi

  if [[ ! -d "$ROOT_DIR/tests" ]]; then
    warn "Missing tests/. Pytest cannot validate the APEX implementation until tests are restored."
    missing=1
  fi

  if [[ ! -d "$ROOT_DIR/scripts" ]]; then
    warn "Missing scripts/. This warning should not appear after auto_setup.sh is added."
    missing=1
  fi

  return "$missing"
}

main() {
  log "Workspace: $ROOT_DIR"
  require_command "$PYTHON_BIN"

  log "Using Python: $($PYTHON_BIN --version)"
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment at $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  else
    log "Reusing virtual environment at $VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  log "Upgrading pip tooling"
  python -m pip install --upgrade pip setuptools wheel

  if [[ -f "$ROOT_DIR/requirements.txt" ]]; then
    log "Installing requirements.txt"
    python -m pip install -r "$ROOT_DIR/requirements.txt"
  else
    warn "requirements.txt not found; skipping dependency install"
  fi

  log "Checking project source tree"
  if check_project_sources; then
    log "Source tree looks runnable."
  else
    warn "Setup completed, but the runnable APEX source tree is incomplete in this checkout."
    warn "Restore apex_core/, tests/, public_site/, and project scripts before continuing Payment-Real implementation."
  fi

  if [[ -d "$ROOT_DIR/tests" ]]; then
    log "Running pytest"
    python -m pytest
  else
    warn "Skipping pytest because tests/ is missing."
  fi

  if [[ -f "$ROOT_DIR/scripts/project_status.py" ]]; then
    log "Writing project status report"
    python "$ROOT_DIR/scripts/project_status.py" || true
  fi

  log "Done."
}

main "$@"
