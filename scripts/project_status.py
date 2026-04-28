#!/usr/bin/env python3
"""Report whether the local checkout contains runnable APEX Factory sources."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "apex_core",
    "tests",
    "scripts",
    "public_site",
]

EXPECTED_SOURCE_MARKERS = [
    "apex_core/orchestrator_v6/studio_entry.py",
    "apex_core/stage_gate/store.py",
    "apex_core/deploy/local_release.py",
    "apex_core/payment/ledger.py",
]

UPLOADED_REPORTS = [
    "BAO_CAO_THI_CONG_v6.md",
    "BAO_CAO_SPRINT_S5_BRIDGE.md",
    "BAO_CAO_SPRINT_UI_STAGE_GATE.md",
    "BAO_CAO_SPRINT_DEPLOY_REAL.md",
    "LENH_THI_CONG_SPRINT_PAYMENT_REAL.md",
]


def exists(relative_path: str) -> bool:
    return (ROOT / relative_path).exists()


def main() -> int:
    required = {path: exists(path) for path in REQUIRED_PATHS}
    markers = {path: exists(path) for path in EXPECTED_SOURCE_MARKERS}
    reports = {path: exists(path) for path in UPLOADED_REPORTS}

    status = {
        "repo_root": str(ROOT),
        "has_required_tree": all(required.values()),
        "has_expected_source_markers": all(markers.values()),
        "required_paths": required,
        "expected_source_markers": markers,
        "local_report_files": reports,
        "documented_stage": (
            "After Deploy-Real and ready for Payment-Real, based on uploaded "
            "reports. Runnable source is required before implementation can continue."
        ),
    }

    print(json.dumps(status, indent=2, ensure_ascii=False))

    if not status["has_expected_source_markers"]:
        print(
            "\nSTATUS: setup files are present, but runnable APEX source files are missing."
        )
        print(
            "NEXT: copy or sync apex_core/, tests/, public_site/, and scripts/ from the full project checkout."
        )
        return 2

    print("\nSTATUS: runnable APEX source markers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
