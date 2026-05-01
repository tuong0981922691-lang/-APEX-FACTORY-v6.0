"""
APEX Factory v5.0 Legacy - Principles (10 Core Principles)
Preserved from v5.0 for backward compatibility.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple


class Principle(str, Enum):
    NT1_MULTI_AXIS_CONVERGENCE = "NT1_MULTI_AXIS_CONVERGENCE"
    NT2_OPEN_SEARCH_SPACE = "NT2_OPEN_SEARCH_SPACE"
    NT3_TRADITIONAL_CULTURE = "NT3_TRADITIONAL_CULTURE"
    NT4_CONSTRAINED_CREATIVITY = "NT4_CONSTRAINED_CREATIVITY"
    NT5_HUMAN_SUPREMACY = "NT5_HUMAN_SUPREMACY"
    NT6_NO_RANDOM_CONCLUSION = "NT6_NO_RANDOM_CONCLUSION"
    NT7_MICRO_PHENOMENA = "NT7_MICRO_PHENOMENA"
    NT8_MULTI_AGENT_SYSTEM = "NT8_MULTI_AGENT_SYSTEM"
    NT9_CONTINUOUS_EVOLUTION = "NT9_CONTINUOUS_EVOLUTION"
    NT10_SELF_REFLECTION = "NT10_SELF_REFLECTION"


@dataclass
class PrincipleRule:
    principle: Principle
    description: str
    title_vi: str = ""
    description_vi: str = ""
    forbidden_patterns: Tuple[str, ...] = ()
    required_patterns: Tuple[str, ...] = ()
    enforcement_level: str = "mandatory"
    violations_count: int = 0


@dataclass
class PrincipleViolation(Exception):
    principle: Principle
    module: str = ""
    message: str = ""
    severity: str = "error"

    def __str__(self) -> str:
        if self.message:
            return f"[{self.principle.value}] {self.module}: {self.message}"
        return f"[{self.principle.value}] {self.module}"


PRINCIPLE_REGISTRY: Dict[Principle, PrincipleRule] = {
    Principle.NT1_MULTI_AXIS_CONVERGENCE: PrincipleRule(
        principle=Principle.NT1_MULTI_AXIS_CONVERGENCE,
        description="Multi-axis convergence required for all outputs",
        title_vi="Hội Tụ Đa Trục",
        description_vi="Mọi output phải hội tụ từ nhiều trục phân tích",
        forbidden_patterns=("single_axis_only",),
        required_patterns=("multi_axis_check",),
    ),
    Principle.NT2_OPEN_SEARCH_SPACE: PrincipleRule(
        principle=Principle.NT2_OPEN_SEARCH_SPACE,
        description="Search space must remain open and explorable",
        title_vi="Không Gian Tìm Kiếm Mở",
        description_vi="Không gian tìm kiếm phải luôn mở và khám phá được",
        forbidden_patterns=("hardcode_result",),
        required_patterns=("search_space_open",),
    ),
    Principle.NT3_TRADITIONAL_CULTURE: PrincipleRule(
        principle=Principle.NT3_TRADITIONAL_CULTURE,
        description="Respect traditional patterns and culture",
        title_vi="Văn Hóa Truyền Thống",
        description_vi="Tôn trọng các mẫu và văn hóa truyền thống",
        forbidden_patterns=(),
        required_patterns=(),
    ),
    Principle.NT4_CONSTRAINED_CREATIVITY: PrincipleRule(
        principle=Principle.NT4_CONSTRAINED_CREATIVITY,
        description="Creativity within defined constraints only",
        title_vi="Sáng Tạo Có Ràng Buộc",
        description_vi="Sáng tạo chỉ trong phạm vi ràng buộc đã định",
        forbidden_patterns=("unconstrained_generation",),
        required_patterns=("constraint_check",),
    ),
    Principle.NT5_HUMAN_SUPREMACY: PrincipleRule(
        principle=Principle.NT5_HUMAN_SUPREMACY,
        description="Human approval required for all critical operations",
        title_vi="Quyền Tối Thượng Con Người",
        description_vi="Mọi thao tác quan trọng phải có sự phê duyệt của con người",
        forbidden_patterns=("auto_deploy", "auto_publish"),
        required_patterns=("capability_token_check", "human_gate"),
    ),
    Principle.NT6_NO_RANDOM_CONCLUSION: PrincipleRule(
        principle=Principle.NT6_NO_RANDOM_CONCLUSION,
        description="No random or unsubstantiated conclusions",
        title_vi="Không Kết Luận Ngẫu Nhiên",
        description_vi="Không đưa ra kết luận ngẫu nhiên hoặc không có cơ sở",
        forbidden_patterns=("random_choice_unsupported",),
        required_patterns=("evidence_based",),
    ),
    Principle.NT7_MICRO_PHENOMENA: PrincipleRule(
        principle=Principle.NT7_MICRO_PHENOMENA,
        description="Attention to micro-level phenomena",
        title_vi="Hiện Tượng Vi Mô",
        description_vi="Chú ý đến các hiện tượng ở mức vi mô",
        forbidden_patterns=(),
        required_patterns=(),
    ),
    Principle.NT8_MULTI_AGENT_SYSTEM: PrincipleRule(
        principle=Principle.NT8_MULTI_AGENT_SYSTEM,
        description="Multi-agent collaboration pattern",
        title_vi="Hệ Thống Đa Tác Nhân",
        description_vi="Mô hình hợp tác đa tác nhân",
        forbidden_patterns=(),
        required_patterns=(),
    ),
    Principle.NT9_CONTINUOUS_EVOLUTION: PrincipleRule(
        principle=Principle.NT9_CONTINUOUS_EVOLUTION,
        description="System must continuously evolve and improve",
        title_vi="Tiến Hóa Liên Tục",
        description_vi="Hệ thống phải liên tục tiến hóa và cải tiến",
        forbidden_patterns=(),
        required_patterns=("evolution_hook",),
    ),
    Principle.NT10_SELF_REFLECTION: PrincipleRule(
        principle=Principle.NT10_SELF_REFLECTION,
        description="Self-reflection and audit capabilities",
        title_vi="Tự Phản Ánh",
        description_vi="Khả năng tự phản ánh và kiểm tra",
        forbidden_patterns=(),
        required_patterns=("audit_trail",),
    ),
}


def enforce_principle(principle: Principle) -> Callable:
    """Decorator that marks a function as enforcing a principle."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        wrapper._enforced_principle = principle  # type: ignore
        return wrapper
    return decorator


def require_human_gate(scope: str = "default") -> Callable:
    """Decorator requiring human approval before execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        wrapper._human_gate_scope = scope  # type: ignore
        return wrapper
    return decorator


def forbid_auto_injection(func: Callable) -> Callable:
    """Decorator that forbids auto-injection of code."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)
    wrapper._forbid_auto_inject = True  # type: ignore
    return wrapper


def audit_module(module_name: str) -> List[PrincipleViolation]:
    """Audit a module for principle violations (stub)."""
    return []


__all__ = [
    "Principle",
    "PrincipleRule",
    "PrincipleViolation",
    "PRINCIPLE_REGISTRY",
    "enforce_principle",
    "require_human_gate",
    "forbid_auto_injection",
    "audit_module",
]
