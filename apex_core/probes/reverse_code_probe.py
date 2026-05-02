"""Reverse-Code Probe (NT20-09 / C8).

Takes code file → produces spec markdown. Compare with original spec → find gaps.
"""


def reverse_to_spec(code_content: str) -> str:
    """Generate spec from code (reverse engineering)."""
    lines = code_content.splitlines()
    functions = [ln.strip() for ln in lines if ln.strip().startswith("def ") or ln.strip().startswith("class ")]
    imports = [ln.strip() for ln in lines if ln.strip().startswith("import ") or ln.strip().startswith("from ")]
    spec = "# Reverse-Engineered Spec\n\n"
    spec += f"## Structure\n- Lines: {len(lines)}\n- Functions/Classes: {len(functions)}\n- Imports: {len(imports)}\n\n"
    spec += "## Functions\n"
    for f in functions:
        spec += f"- {f}\n"
    return spec


def compare_specs(original_spec: str, reversed_spec: str) -> list[str]:
    """Compare original spec with reversed spec, find gaps."""
    original_lines = set(original_spec.lower().splitlines())
    reversed_lines = set(reversed_spec.lower().splitlines())
    gaps = []
    for line in original_lines:
        if line.strip() and line not in reversed_lines:
            gaps.append(f"Missing in implementation: {line.strip()[:100]}")
    return gaps[:20]
