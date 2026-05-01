"""
APEX FACTORY v6.0 - Foundation Extension
File: principles_v6.py

Mục đích: Kế thừa nguyên vẹn 10 Nguyên Tắc từ v5.0 (legacy) và MỞ RỘNG
          thêm 2 Nguyên Tắc mới dành riêng cho miền sản xuất Web/App/Video.

NT11 - Design System Integrity:
    Mọi component phải tham chiếu token trong TokenRegistry.
    Không hardcode giá trị màu/spacing/typography trực tiếp.

NT12 - Accessibility Non-Negotiable:
    Không có ngoại lệ cho a11y contract. WCAG 2.2 AA là sàn tối thiểu.
    Thiếu aria/keyboard map → build bị block (không phải warning).

Cách import:
    from apex_core.foundation.principles_v6 import (
        Principle, PrincipleV6, PRINCIPLE_REGISTRY_V6,
        enforce_principle, require_human_gate, forbid_auto_injection,
    )

Enum `PrincipleV6` là UNION của `Principle` cũ + 2 giá trị mới.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Tuple

# Kế thừa nguyên vẹn từ legacy
from apex_core.legacy.foundation.principles import (
    PRINCIPLE_REGISTRY as _LEGACY_REGISTRY,
)
from apex_core.legacy.foundation.principles import (
    Principle,
    PrincipleRule,
    PrincipleViolation,
    audit_module,
    enforce_principle,
    forbid_auto_injection,
    require_human_gate,
)

# ============================================================
# 1. EXTEND PRINCIPLE ENUM
# ============================================================

class PrincipleV6(str, Enum):
    """
    V6 principle set = toàn bộ NT1..NT10 cũ + NT11, NT12 mới.
    Giá trị string khớp enum cũ để decorator vẫn nhận diện.
    """
    NT1_MULTI_AXIS_CONVERGENCE = "NT1_MULTI_AXIS_CONVERGENCE"
    NT2_OPEN_SEARCH_SPACE = "NT2_OPEN_SEARCH_SPACE"
    NT3_TRADITIONAL_CULTURE = "NT3_TRADITIONAL_CULTURE"
    NT4_CONSTRAINED_CREATIVITY = "NT4_CONSTRAINED_CREATIVITY"
    NT5_HUMAN_SUPREMACY = "NT5_HUMAN_SUPREMACY"
    NT6_NO_RANDOM_CONCLUSION = "NT6_NO_RANDOM_CONCLUSION"
    NT7_MICRO_PHENOMENA = "NT7_MICRO_PHENOMENA"
    NT8_MULTI_AGENT_SYSTEM = "NT8_MULTI_AGENT_SYSTEM"
    NT9_ROUND_TABLE_IS_CRITIC = "NT9_ROUND_TABLE_IS_CRITIC"
    NT10_PLUGIN_PHENOMENA = "NT10_PLUGIN_PHENOMENA"
    # ---- v6 new ----
    NT11_DESIGN_SYSTEM_INTEGRITY = "NT11_DESIGN_SYSTEM_INTEGRITY"
    NT12_ACCESSIBILITY_NON_NEGOTIABLE = "NT12_ACCESSIBILITY_NON_NEGOTIABLE"


# ============================================================
# 2. RULE DESCRIPTORS CHO 2 NT MỚI
# ============================================================

@dataclass(frozen=True)
class PrincipleRuleV6:
    principle: PrincipleV6
    title_vi: str
    description_vi: str
    forbidden_patterns: Tuple[str, ...]
    required_patterns: Tuple[str, ...]


NT11_RULE = PrincipleRuleV6(
    principle=PrincipleV6.NT11_DESIGN_SYSTEM_INTEGRITY,
    title_vi="Tính Toàn Vẹn Design System",
    description_vi=(
        "Mọi ComponentSpec phải dùng token trong TokenRegistry. "
        "Không hardcode color/spacing/typography trực tiếp trong source. "
        "TokenRegistry bị freeze sau khi build để chặn drift runtime."
    ),
    forbidden_patterns=(
        "hardcoded_hex_color_in_component",
        "hardcoded_px_spacing_in_component",
        "token_registry_mutation_after_freeze",
    ),
    required_patterns=(
        "reference_token_by_id",
        "token_registry_freeze_on_boot",
        "validate_component_tokens_against_registry",
    ),
)

NT12_RULE = PrincipleRuleV6(
    principle=PrincipleV6.NT12_ACCESSIBILITY_NON_NEGOTIABLE,
    title_vi="Tiếp Cận (A11y) Không Nhân Nhượng",
    description_vi=(
        "WCAG 2.2 AA là sàn tối thiểu. Mọi ComponentSpec phải có "
        "A11yContract đầy đủ (role + keyboard_map + contrast). "
        "Vi phạm = ERROR chặn build, KHÔNG phải warning."
    ),
    forbidden_patterns=(
        "missing_aria_label_on_img",
        "contrast_ratio_below_4.5",
        "keyboard_trap_without_escape",
        "button_without_keyboard_handler",
    ),
    required_patterns=(
        "explicit_a11y_contract_per_component",
        "focus_ring_required_on_interactive",
        "screen_reader_announcement_for_state_change",
    ),
)


# ============================================================
# 3. UNIFIED REGISTRY (kế thừa + mở rộng)
# ============================================================

def _extend_legacy_with_v6() -> Dict[str, Any]:
    """Gộp legacy registry + NT11 + NT12 thành 1 dict thống nhất."""
    unified: Dict[str, Any] = {}
    # Legacy entries
    for p, rule in _LEGACY_REGISTRY.items():
        unified[p.value] = {
            "principle": p.value,
            "title_vi": rule.title_vi,
            "description_vi": rule.description_vi,
            "forbidden_patterns": list(rule.forbidden_patterns),
            "required_patterns": list(rule.required_patterns),
            "source": "v5.0_legacy",
        }
    # V6 additions
    for r in (NT11_RULE, NT12_RULE):
        unified[r.principle.value] = {
            "principle": r.principle.value,
            "title_vi": r.title_vi,
            "description_vi": r.description_vi,
            "forbidden_patterns": list(r.forbidden_patterns),
            "required_patterns": list(r.required_patterns),
            "source": "v6.0_factory",
        }
    return unified


PRINCIPLE_REGISTRY_V6: Dict[str, Any] = _extend_legacy_with_v6()


# ============================================================
# 4. VIOLATION CHECKER HELPERS (cho code Phase 1+ dùng)
# ============================================================

def raise_nt11_if(condition: bool, context: str) -> None:
    if condition:
        raise PrincipleViolation(
            # Lưu ý: PrincipleViolation legacy lấy enum cũ; ta pass NT5
            # để không break signature, chi tiết NT11 ghi vào context.
            Principle.NT5_HUMAN_SUPREMACY,
            f"[NT11 Design System Integrity] {context}",
        )


def raise_nt12_if(condition: bool, context: str) -> None:
    if condition:
        raise PrincipleViolation(
            Principle.NT5_HUMAN_SUPREMACY,
            f"[NT12 Accessibility Non-Negotiable] {context}",
        )


# ============================================================
# 5. COMPATIBILITY ENFORCE DECORATOR (accept cả enum cũ và mới)
# ============================================================

def enforce_principle_v6(principle: Any) -> Callable:
    """
    Decorator tương thích: chấp nhận cả `Principle` (v5.0) lẫn `PrincipleV6` (v6.0).
    Thuộc tính `__apex_principles__` trên function được dùng cho audit.
    """
    def decorator(fn: Callable) -> Callable:
        principles_attr = getattr(fn, "__apex_principles__", set())
        if isinstance(principle, Enum):
            principles_attr.add(principle.value)
        else:
            principles_attr.add(str(principle))
        fn.__apex_principles__ = principles_attr
        return fn
    return decorator


# ============================================================
# 6. SANITY CHECK
# ============================================================

def principles_v6_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    # Tất cả NT1..NT10 legacy phải có mặt trong registry v6
    legacy_keys = {p.value for p in Principle}
    v6_keys = set(PRINCIPLE_REGISTRY_V6.keys())
    checks["legacy_10_inherited"] = legacy_keys.issubset(v6_keys)

    # NT11, NT12 có mặt
    checks["nt11_present"] = PrincipleV6.NT11_DESIGN_SYSTEM_INTEGRITY.value in v6_keys
    checks["nt12_present"] = PrincipleV6.NT12_ACCESSIBILITY_NON_NEGOTIABLE.value in v6_keys

    # Decorator v6 hoạt động
    @enforce_principle_v6(PrincipleV6.NT11_DESIGN_SYSTEM_INTEGRITY)
    def dummy():
        return True
    checks["decorator_v6_attached"] = (
        "NT11_DESIGN_SYSTEM_INTEGRITY" in getattr(dummy, "__apex_principles__", set())
    )

    # Raise helpers
    try:
        raise_nt11_if(True, "test")
        checks["nt11_raises"] = False
    except PrincipleViolation as e:
        checks["nt11_raises"] = "NT11" in str(e)

    try:
        raise_nt12_if(True, "test")
        checks["nt12_raises"] = False
    except PrincipleViolation as e:
        checks["nt12_raises"] = "NT12" in str(e)

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    # Kế thừa từ legacy - re-export để v6 code không cần import 2 nơi
    "Principle",
    "PrincipleRule",
    "PrincipleViolation",
    "enforce_principle",
    "require_human_gate",
    "forbid_auto_injection",
    "audit_module",
    # V6 new
    "PrincipleV6",
    "PrincipleRuleV6",
    "NT11_RULE",
    "NT12_RULE",
    "PRINCIPLE_REGISTRY_V6",
    "raise_nt11_if",
    "raise_nt12_if",
    "enforce_principle_v6",
    "principles_v6_sanity_check",
]
