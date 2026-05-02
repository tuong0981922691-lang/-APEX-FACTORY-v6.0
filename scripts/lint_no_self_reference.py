"""NT26 — Anonymous Architect enforcement.

Scans code/reports/public_site for model name self-references.
Excludes: reports/owner_directives/, reports/blueprints/, manifest files.

Exit code 0 = clean. Exit code 1 = violations found.
"""
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERN = re.compile(
    r"\b(4\.7|claude|sonnet|gpt|codex|gemini)\b",
    re.IGNORECASE,
)

SCAN_DIRS = ["apex_core", "public_site", "tests"]
EXCLUDE_DIRS = {"reports/owner_directives", "reports/blueprints", "node_modules", "venv", ".git", "__pycache__"}
SCAN_EXTENSIONS = {".py", ".html", ".js", ".css", ".md", ".txt"}


def scan_file(path: Path) -> list[str]:
    """Scan a single file for forbidden patterns."""
    violations = []
    try:
        content = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return []
    for i, line in enumerate(content.splitlines(), 1):
        matches = FORBIDDEN_PATTERN.findall(line)
        if matches:
            violations.append(f"{path}:{i}: found {matches}")
    return violations


def main() -> int:
    """Run the lint scan."""
    root = Path(__file__).parent.parent
    all_violations = []

    for scan_dir in SCAN_DIRS:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for file_path in dir_path.rglob("*"):
            if file_path.suffix not in SCAN_EXTENSIONS:
                continue
            rel = str(file_path.relative_to(root))
            if any(rel.startswith(excl) for excl in EXCLUDE_DIRS):
                continue
            violations = scan_file(file_path)
            all_violations.extend(violations)

    if all_violations:
        print(f"NT26 VIOLATION: {len(all_violations)} self-reference(s) found:")
        for v in all_violations[:20]:
            print(f"  {v}")
        return 1

    print("NT26 lint: CLEAN (0 self-references)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
