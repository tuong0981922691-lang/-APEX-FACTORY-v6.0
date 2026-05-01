"""
APEX FACTORY v6.0 - Foundation Extension
File: domain_types.py

Mục đích: Đăng ký các DomainType mà Xưởng có thể sản xuất + capabilities.
          Là SOURCE OF TRUTH cho router "brief → đúng factory".
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

# ============================================================
# 1. DOMAIN TYPE
# ============================================================

class DomainType(str, Enum):
    """Các miền sản xuất Xưởng hỗ trợ. Web/App/Video theo thứ tự ưu tiên C2."""
    WEB = "web"                         # Static site + SPA
    APP_MOBILE = "app_mobile"           # React Native / Flutter
    APP_DESKTOP = "app_desktop"         # Electron / Tauri
    VIDEO = "video"                     # Reel / ad / explainer
    IMAGE = "image"                     # poster / banner / thumbnail
    MIXED = "mixed"                     # Web có video embed, App có image gen, v.v.


# ============================================================
# 2. DOMAIN CAPABILITY
# ============================================================

@dataclass(frozen=True)
class DomainCapability:
    """Thông tin năng lực của 1 domain: factory nào xử lý, ràng buộc gì."""
    domain: DomainType
    factory_module_path: str            # "apex_core.factories.web_factory"
    factory_class_name: str             # "WebFactory"
    supported_render_targets: Tuple[str, ...] = ()      # giá trị của RenderTarget
    supported_media_formats: Tuple[str, ...] = ()
    requires_llm_borrowing: bool = False
    requires_external_tool: Tuple[str, ...] = ()        # "ffmpeg", "node", "docker"
    priority: int = 999                                  # thứ tự C2 ưu tiên (thấp = trước)
    enabled_by_default: bool = True
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "factory_module_path": self.factory_module_path,
            "factory_class_name": self.factory_class_name,
            "supported_render_targets": list(self.supported_render_targets),
            "supported_media_formats": list(self.supported_media_formats),
            "requires_llm_borrowing": self.requires_llm_borrowing,
            "requires_external_tool": list(self.requires_external_tool),
            "priority": self.priority,
            "enabled_by_default": self.enabled_by_default,
            "notes": self.notes,
        }


# ============================================================
# 3. DEFAULT REGISTRY (theo thứ tự C2 duyệt: Web → App → Video)
# ============================================================

DEFAULT_DOMAIN_CAPABILITIES: Tuple[DomainCapability, ...] = (
    DomainCapability(
        domain=DomainType.WEB,
        factory_module_path="apex_core.factories.web_factory",
        factory_class_name="WebFactory",
        supported_render_targets=("react", "vue", "svelte", "html_static"),
        supported_media_formats=(),
        requires_llm_borrowing=True,
        requires_external_tool=("node", "npm"),
        priority=1,
        enabled_by_default=True,
        notes="React + TypeScript + Tailwind là stack ưu tiên",
    ),
    DomainCapability(
        domain=DomainType.APP_MOBILE,
        factory_module_path="apex_core.factories.mobile_factory",
        factory_class_name="MobileFactory",
        supported_render_targets=("react_native", "flutter"),
        supported_media_formats=(),
        requires_llm_borrowing=True,
        requires_external_tool=("node", "npm"),
        priority=2,
        enabled_by_default=False,        # bật ở Phase 6
        notes="Phase 6 mới mở",
    ),
    DomainCapability(
        domain=DomainType.APP_DESKTOP,
        factory_module_path="apex_core.factories.desktop_factory",
        factory_class_name="DesktopFactory",
        supported_render_targets=("react",),
        supported_media_formats=(),
        requires_llm_borrowing=True,
        requires_external_tool=("node", "npm"),
        priority=3,
        enabled_by_default=False,
        notes="Electron / Tauri wrapper cho web stack",
    ),
    DomainCapability(
        domain=DomainType.VIDEO,
        factory_module_path="apex_core.factories.video_factory",
        factory_class_name="VideoFactory",
        supported_render_targets=(),
        supported_media_formats=("mp4", "webm", "mov"),
        requires_llm_borrowing=True,
        requires_external_tool=("ffmpeg",),
        priority=4,
        enabled_by_default=False,
        notes="Phase 6",
    ),
    DomainCapability(
        domain=DomainType.IMAGE,
        factory_module_path="apex_core.factories.image_factory",
        factory_class_name="ImageFactory",
        supported_render_targets=(),
        supported_media_formats=("png", "jpg", "webp", "svg"),
        requires_llm_borrowing=True,
        requires_external_tool=(),
        priority=5,
        enabled_by_default=False,
        notes="Phase 6",
    ),
    DomainCapability(
        domain=DomainType.MIXED,
        factory_module_path="apex_core.factories.mixed_factory",
        factory_class_name="MixedFactory",
        supported_render_targets=("react",),
        supported_media_formats=("png", "mp4"),
        requires_llm_borrowing=True,
        requires_external_tool=(),
        priority=99,
        enabled_by_default=False,
    ),
)


# ============================================================
# 4. DOMAIN REGISTRY
# ============================================================

class DomainRegistry:
    """
    Registry domain cho toàn hệ thống. C2 có thể enable/disable
    từng domain runtime (không code cứng trong Brain).
    """

    def __init__(self, capabilities: Optional[Sequence[DomainCapability]] = None):
        caps = list(capabilities) if capabilities else list(DEFAULT_DOMAIN_CAPABILITIES)
        self._by_domain: Dict[DomainType, DomainCapability] = {c.domain: c for c in caps}
        self._enabled: Dict[DomainType, bool] = {
            c.domain: c.enabled_by_default for c in caps
        }

    def register(self, cap: DomainCapability) -> None:
        self._by_domain[cap.domain] = cap
        self._enabled.setdefault(cap.domain, cap.enabled_by_default)

    def get(self, domain: DomainType) -> Optional[DomainCapability]:
        return self._by_domain.get(domain)

    def require(self, domain: DomainType) -> DomainCapability:
        cap = self.get(domain)
        if cap is None:
            raise KeyError(f"Domain not registered: {domain.value}")
        return cap

    def enable(self, domain: DomainType) -> None:
        if domain not in self._by_domain:
            raise KeyError(f"Unknown domain: {domain.value}")
        self._enabled[domain] = True

    def disable(self, domain: DomainType) -> None:
        self._enabled[domain] = False

    def is_enabled(self, domain: DomainType) -> bool:
        return self._enabled.get(domain, False)

    def enabled_domains(self) -> List[DomainType]:
        return [d for d, on in self._enabled.items() if on]

    def list_by_priority(self, enabled_only: bool = True) -> List[DomainCapability]:
        items = list(self._by_domain.values())
        if enabled_only:
            items = [c for c in items if self._enabled.get(c.domain, False)]
        return sorted(items, key=lambda c: c.priority)

    def summary(self) -> Dict[str, Any]:
        return {
            "total_domains": len(self._by_domain),
            "enabled": [d.value for d in self.enabled_domains()],
            "priority_order": [c.domain.value for c in self.list_by_priority(enabled_only=False)],
        }


# ============================================================
# 5. BRIEF → DOMAIN ROUTER HEURISTIC (placeholder; full ở Phase 1 - B1)
# ============================================================

KEYWORD_TO_DOMAIN: Dict[DomainType, FrozenSet[str]] = {
    DomainType.WEB: frozenset({
        "landing", "website", "web", "site", "dashboard", "spa",
        "trang web", "trang đích", "web app",
    }),
    DomainType.APP_MOBILE: frozenset({
        "mobile app", "ios", "android", "react native", "flutter",
        "ứng dụng di động", "app điện thoại",
    }),
    DomainType.APP_DESKTOP: frozenset({
        "desktop app", "electron", "tauri", "windows app", "macos app",
        "ứng dụng máy tính",
    }),
    DomainType.VIDEO: frozenset({
        "video", "reel", "short", "youtube", "tiktok", "vlog",
        "quảng cáo video", "phim ngắn",
    }),
    DomainType.IMAGE: frozenset({
        "banner", "poster", "thumbnail", "infographic", "social card",
        "ảnh bìa", "ảnh quảng cáo",
    }),
}


def heuristic_detect_domain(brief_text: str) -> Tuple[DomainType, float]:
    """
    Bắt domain thô từ brief. Trả (domain, confidence 0..1).
    Phase 1 B1 IntentIngestor sẽ dùng parser mạnh hơn thay thế.
    """
    if not brief_text:
        return DomainType.WEB, 0.3
    lower = brief_text.lower()
    scores: Dict[DomainType, int] = {}
    for domain, keywords in KEYWORD_TO_DOMAIN.items():
        count = sum(1 for kw in keywords if kw in lower)
        if count > 0:
            scores[domain] = count
    if not scores:
        return DomainType.WEB, 0.3     # fallback
    best = max(scores.items(), key=lambda kv: kv[1])
    total = sum(scores.values())
    confidence = min(0.95, best[1] / max(total, 1))
    return best[0], round(confidence, 3)


# ============================================================
# 6. SANITY CHECK
# ============================================================

def domain_types_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    reg = DomainRegistry()
    checks["web_enabled_by_default"] = reg.is_enabled(DomainType.WEB)
    checks["video_disabled_by_default"] = not reg.is_enabled(DomainType.VIDEO)
    checks["priority_web_first"] = (
        reg.list_by_priority(enabled_only=False)[0].domain == DomainType.WEB
    )

    reg.enable(DomainType.VIDEO)
    checks["video_can_enable"] = reg.is_enabled(DomainType.VIDEO)

    d, conf = heuristic_detect_domain("Tôi muốn làm 1 landing page React đẹp")
    checks["heuristic_detect_web"] = d == DomainType.WEB and conf > 0

    d, conf = heuristic_detect_domain("Tạo video reel TikTok 15 giây")
    checks["heuristic_detect_video"] = d == DomainType.VIDEO

    d, conf = heuristic_detect_domain("")
    checks["heuristic_fallback"] = d == DomainType.WEB

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "DomainType",
    "DomainCapability",
    "DEFAULT_DOMAIN_CAPABILITIES",
    "DomainRegistry",
    "KEYWORD_TO_DOMAIN",
    "heuristic_detect_domain",
    "domain_types_sanity_check",
]
