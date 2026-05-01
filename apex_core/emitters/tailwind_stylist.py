"""
APEX FACTORY v6.0 - Emitter Layer
File: tailwind_stylist.py

Mục đích: Biến DesignToken (TokenRegistry) → Tailwind class + tailwind.config.js.
    Lý do chọn Tailwind (chốt theo C2):
      - Utility-first → nhỏ bundle, không CSS-in-JS overhead
      - Arbitrary values `bg-[#2563EB]` khi cần
      - tailwind.config.js là truth source cho design token

Triết lý NT11 (Design System Integrity):
    Component KHÔNG được hardcode hex/px trực tiếp trong JSX.
    Phải đi qua tailwind class tương ứng với token, hoặc CSS variable.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from apex_core.foundation.ontology_ui import (
    ColorToken,
    MotionToken,
    RadiusToken,
    ShadowToken,
    SpacingToken,
    TokenRegistry,
    TokenRole,
    TypographyToken,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
    raise_nt11_if,
)

# ============================================================
# 0. VERSION
# ============================================================

TAILWIND_STYLIST_VERSION = "6.0.0"
TAILWIND_MIN_VERSION = "3.4.0"


# ============================================================
# 1. TOKEN → CLASS MAPPINGS
# ============================================================

# Role → Tailwind semantic utility prefix
# Tailwind không có role-based naming built-in, nên ta dùng custom name
# mapped qua config (xem _build_config).
ROLE_TO_CONFIG_KEY: Dict[TokenRole, str] = {
    TokenRole.PRIMARY: "primary",
    TokenRole.SECONDARY: "secondary",
    TokenRole.ACCENT: "accent",
    TokenRole.SURFACE: "surface",
    TokenRole.SURFACE_ALT: "surface-alt",
    TokenRole.BACKGROUND: "background",
    TokenRole.TEXT: "text",
    TokenRole.TEXT_MUTED: "text-muted",
    TokenRole.BORDER: "border",
    TokenRole.SUCCESS: "success",
    TokenRole.WARNING: "warning",
    TokenRole.DANGER: "danger",
    TokenRole.INFO: "info",
    TokenRole.NEUTRAL: "neutral",
}


# ============================================================
# 2. CLASS EMIT HELPERS
# ============================================================

_ID_SAFE = re.compile(r"[^a-z0-9-]")


def _slugify_token_id(token_id: str) -> str:
    """
    'brand.primary.600' → 'brand-primary-600' (Tailwind-friendly key)
    """
    s = token_id.lower().replace(".", "-").replace("_", "-")
    return _ID_SAFE.sub("", s)


# ============================================================
# 3. TOKEN CLASS RESOLVER
# ============================================================

@dataclass(frozen=True)
class ResolvedClass:
    """1 utility class đã resolve từ token reference."""
    utility: str                        # "bg-brand-primary-600" | "text-[#2563EB]"
    source_token_id: Optional[str]      # None nếu arbitrary
    fallback_used: bool = False


class ClassResolver:
    """
    Resolve 1 (token_id, utility_prefix) → Tailwind class.
    Ví dụ: resolve_color("brand.primary.600", "bg") → "bg-brand-primary-600"
    """

    def __init__(self, registry: TokenRegistry):
        self.registry = registry

    @enforce_principle_v6(PrincipleV6.NT11_DESIGN_SYSTEM_INTEGRITY)
    def resolve_color(
        self, token_id: str, utility_prefix: str
    ) -> ResolvedClass:
        """
        utility_prefix: "bg" | "text" | "border" | "ring" | ...
        """
        tok = self.registry.get(token_id)
        if tok is None:
            # NT11 strict: chưa có trong registry → KHÔNG cho arbitrary
            # mà raise để Commander biết cần add token trước.
            raise_nt11_if(
                True,
                f"Color token '{token_id}' not in registry. "
                f"Add via TokenRegistry.add() before emit.",
            )
        if not isinstance(tok, ColorToken):
            raise ValueError(f"Token '{token_id}' is not a ColorToken")
        slug = _slugify_token_id(token_id)
        return ResolvedClass(
            utility=f"{utility_prefix}-{slug}",
            source_token_id=token_id,
        )

    def resolve_spacing(
        self, token_id: str, utility_prefix: str
    ) -> ResolvedClass:
        """
        utility_prefix: "p" | "px" | "py" | "m" | "gap" | "space-x" | ...
        """
        tok = self.registry.get(token_id)
        if tok is None:
            raise_nt11_if(True, f"Spacing token '{token_id}' not in registry")
        if not isinstance(tok, SpacingToken):
            raise ValueError(f"Token '{token_id}' is not SpacingToken")
        slug = _slugify_token_id(token_id)
        return ResolvedClass(
            utility=f"{utility_prefix}-{slug}",
            source_token_id=token_id,
        )

    def resolve_radius(self, token_id: str) -> ResolvedClass:
        tok = self.registry.get(token_id)
        if tok is None:
            raise_nt11_if(True, f"Radius token '{token_id}' not in registry")
        if not isinstance(tok, RadiusToken):
            raise ValueError(f"Token '{token_id}' is not RadiusToken")
        slug = _slugify_token_id(token_id)
        return ResolvedClass(utility=f"rounded-{slug}", source_token_id=token_id)

    def resolve_shadow(self, token_id: str) -> ResolvedClass:
        tok = self.registry.get(token_id)
        if tok is None:
            raise_nt11_if(True, f"Shadow token '{token_id}' not in registry")
        if not isinstance(tok, ShadowToken):
            raise ValueError(f"Token '{token_id}' is not ShadowToken")
        slug = _slugify_token_id(token_id)
        return ResolvedClass(utility=f"shadow-{slug}", source_token_id=token_id)

    def resolve_motion(self, token_id: str) -> ResolvedClass:
        tok = self.registry.get(token_id)
        if tok is None:
            raise_nt11_if(True, f"Motion token '{token_id}' not in registry")
        if not isinstance(tok, MotionToken):
            raise ValueError(f"Token '{token_id}' is not MotionToken")
        slug = _slugify_token_id(token_id)
        return ResolvedClass(utility=f"duration-{slug}", source_token_id=token_id)

    def resolve_typography(self, token_id: str) -> List[ResolvedClass]:
        """
        Typography = bundle nhiều class: text-<size>, font-<weight>, leading-<line-height>
        """
        tok = self.registry.get(token_id)
        if tok is None:
            raise_nt11_if(True, f"Typography token '{token_id}' not in registry")
        if not isinstance(tok, TypographyToken):
            raise ValueError(f"Token '{token_id}' is not TypographyToken")
        slug = _slugify_token_id(token_id)
        return [
            ResolvedClass(utility=f"text-{slug}", source_token_id=token_id),
            ResolvedClass(utility=f"font-weight-{tok.font_weight}", source_token_id=token_id),
        ]


# ============================================================
# 4. CLASS LIST COMPOSER (conditional + dedup)
# ============================================================

class ClassList:
    """
    Compose nhiều class, dedup, hỗ trợ conditional.
    Kết quả render ra string dùng cho className.
    """

    def __init__(self, initial: Optional[Sequence[str]] = None):
        self._classes: List[str] = list(initial or [])

    def add(self, *classes: str) -> "ClassList":
        for c in classes:
            if c and c.strip():
                self._classes.append(c.strip())
        return self

    def add_if(self, condition: bool, *classes: str) -> "ClassList":
        if condition:
            self.add(*classes)
        return self

    def add_resolved(self, *resolved: ResolvedClass) -> "ClassList":
        for r in resolved:
            self.add(r.utility)
        return self

    def dedup(self) -> "ClassList":
        seen: set = set()
        out: List[str] = []
        for c in self._classes:
            if c not in seen:
                seen.add(c)
                out.append(c)
        self._classes = out
        return self

    def render(self) -> str:
        self.dedup()
        return " ".join(self._classes)

    def to_list(self) -> List[str]:
        self.dedup()
        return list(self._classes)

    def __str__(self) -> str:
        return self.render()


# ============================================================
# 5. TAILWIND CONFIG BUILDER
# ============================================================

@dataclass
class TailwindTheme:
    """Giá trị truyền vào `theme.extend.{colors,spacing,...}` của tailwind.config.js."""
    colors: Dict[str, str] = field(default_factory=dict)                # "brand-primary-600": "#2563EB"
    spacing: Dict[str, str] = field(default_factory=dict)               # "space-4": "1rem"
    border_radius: Dict[str, str] = field(default_factory=dict)
    box_shadow: Dict[str, str] = field(default_factory=dict)
    transition_duration: Dict[str, str] = field(default_factory=dict)
    font_size: Dict[str, List[Any]] = field(default_factory=dict)       # [size, {lineHeight, letterSpacing}]
    font_family: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if self.colors:             out["colors"] = self.colors
        if self.spacing:            out["spacing"] = self.spacing
        if self.border_radius:      out["borderRadius"] = self.border_radius
        if self.box_shadow:         out["boxShadow"] = self.box_shadow
        if self.transition_duration: out["transitionDuration"] = self.transition_duration
        if self.font_size:          out["fontSize"] = self.font_size
        if self.font_family:        out["fontFamily"] = self.font_family
        return out


class TailwindConfigBuilder:
    """
    Duyệt TokenRegistry, build TailwindTheme + render tailwind.config.js.
    """

    def __init__(self, registry: TokenRegistry):
        self.registry = registry

    def build_theme(self) -> TailwindTheme:
        theme = TailwindTheme()

        # Registry nội bộ: duyệt tất cả bucket
        # (TokenRegistry có all_ids() nhưng không phân loại, ta dùng .get() + isinstance)
        for tid in self.registry.all_ids():
            tok = self.registry.get(tid)
            slug = _slugify_token_id(tid)
            if isinstance(tok, ColorToken):
                value = tok.value
                if tok.dark_mode_variant:
                    # Tailwind dark-mode: dùng CSS var hoặc dark: prefix ở component
                    # Ở config ta dùng giá trị light; dark sẽ override qua :root.dark
                    value = tok.value
                theme.colors[slug] = value
            elif isinstance(tok, SpacingToken):
                theme.spacing[slug] = f"{tok.value_rem}rem"
            elif isinstance(tok, RadiusToken):
                theme.border_radius[slug] = f"{tok.value_rem}rem"
            elif isinstance(tok, ShadowToken):
                # Format: "offset-x offset-y blur spread color"
                # Ta dùng CSS var để resolve color từ token name
                color_ref = f"var(--color-{_slugify_token_id(tok.color_ref)})"
                inset = "inset " if tok.inset else ""
                theme.box_shadow[slug] = (
                    f"{inset}{tok.offset_x_rem}rem {tok.offset_y_rem}rem "
                    f"{tok.blur_rem}rem {tok.spread_rem}rem {color_ref}"
                )
            elif isinstance(tok, MotionToken):
                theme.transition_duration[slug] = f"{tok.duration_ms}ms"
            elif isinstance(tok, TypographyToken):
                theme.font_size[slug] = [
                    f"{tok.font_size_rem}rem",
                    {
                        "lineHeight": str(tok.line_height),
                        "letterSpacing": f"{tok.letter_spacing_em}em",
                    },
                ]

        return theme

    def render_config(
        self,
        content_globs: Optional[Sequence[str]] = None,
        dark_mode: str = "class",
        plugins: Optional[Sequence[str]] = None,
    ) -> str:
        """
        Render tailwind.config.js content.
        """
        theme = self.build_theme()
        content = list(content_globs or [
            "./src/**/*.{js,ts,jsx,tsx,html}",
            "./index.html",
        ])
        plugins = list(plugins or [])

        extend_dict = theme.to_dict()
        extend_json = json.dumps(extend_dict, indent=2, ensure_ascii=False)

        plugins_str = (
            "[" + ", ".join(f"require('{p}')" for p in plugins) + "]"
            if plugins else "[]"
        )

        content_json = json.dumps(content, indent=2)

        return (
            "/** @type {import('tailwindcss').Config} */\n"
            "// Auto-generated by APEX FACTORY v6.0 - TailwindConfigBuilder\n"
            "// Token count: "
            f"{sum(self.registry.summary().get(k, 0) for k in ('colors','spacing','radius','shadow','motion','typography'))}\n"
            "// Registry fingerprint: "
            f"{self.registry.fingerprint()[:16]}\n"
            "module.exports = {\n"
            f"  content: {content_json},\n"
            f"  darkMode: '{dark_mode}',\n"
            "  theme: {\n"
            f"    extend: {extend_json}\n"
            "  },\n"
            f"  plugins: {plugins_str},\n"
            "};\n"
        )

    def render_css_variables(self) -> str:
        """
        CSS :root biến cho color (dùng bởi box-shadow token tham chiếu).
        Đặt trong src/styles/tokens.css.
        """
        lines = [
            "/* Auto-generated by APEX FACTORY v6.0 - TailwindStylist */",
            ":root {",
        ]
        for tid in self.registry.all_ids():
            tok = self.registry.get(tid)
            if isinstance(tok, ColorToken):
                slug = _slugify_token_id(tid)
                lines.append(f"  --color-{slug}: {tok.value};")
        lines.append("}")

        # Dark mode override
        dark_lines: List[str] = []
        for tid in self.registry.all_ids():
            tok = self.registry.get(tid)
            if isinstance(tok, ColorToken) and tok.dark_mode_variant:
                slug = _slugify_token_id(tid)
                dark_lines.append(f"  --color-{slug}: {tok.dark_mode_variant};")
        if dark_lines:
            lines.append("")
            lines.append(".dark {")
            lines.extend(dark_lines)
            lines.append("}")

        return "\n".join(lines) + "\n"


# ============================================================
# 6. DYNAMIC CLASS SAFELIST
# ============================================================

class SafelistBuilder:
    """
    Thu thập các class có thể sinh runtime (conditional) để Tailwind JIT
    không purge nhầm. Đặt vào tailwind.config.js `safelist`.
    """

    def __init__(self):
        self._entries: List[str] = []

    def add(self, pattern: str) -> "SafelistBuilder":
        self._entries.append(pattern)
        return self

    def add_many(self, patterns: Sequence[str]) -> "SafelistBuilder":
        self._entries.extend(patterns)
        return self

    def render_js_array(self) -> str:
        return "[" + ", ".join(f"'{p}'" for p in self._entries) + "]"

    def to_list(self) -> List[str]:
        return list(dict.fromkeys(self._entries))   # dedup, giữ thứ tự


# ============================================================
# 7. SANITY CHECK
# ============================================================

def tailwind_stylist_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    reg = TokenRegistry()
    reg.add(ColorToken(
        token_id="brand.primary.600",
        value="#2563EB",
        role=TokenRole.PRIMARY,
        dark_mode_variant="#3B82F6",
    ))
    reg.add(ColorToken(
        token_id="surface.base",
        value="#FFFFFF",
        role=TokenRole.SURFACE,
    ))
    reg.add(SpacingToken(token_id="space.4", scale_index=4, value_rem=1.0))
    reg.add(RadiusToken(token_id="radius.md", value_rem=0.375))
    reg.add(ShadowToken(
        token_id="shadow.md",
        offset_x_rem=0, offset_y_rem=0.25,
        blur_rem=0.5, spread_rem=0,
        color_ref="brand.primary.600",
    ))
    reg.add(MotionToken(token_id="motion.fast", duration_ms=150, easing="ease-out"))
    reg.freeze()

    # Class resolver
    resolver = ClassResolver(reg)
    bg = resolver.resolve_color("brand.primary.600", "bg")
    checks["color_resolved"] = bg.utility == "bg-brand-primary-600"

    spacing = resolver.resolve_spacing("space.4", "px")
    checks["spacing_resolved"] = spacing.utility == "px-space-4"

    try:
        resolver.resolve_color("not.in.registry", "bg")
        checks["nt11_raises"] = False
    except Exception:
        checks["nt11_raises"] = True

    # ClassList compose
    cls = ClassList()
    cls.add("inline-flex", "items-center")
    cls.add_if(True, "gap-2")
    cls.add_if(False, "hidden")
    cls.add_resolved(bg, spacing)
    rendered = cls.render()
    checks["classlist_render"] = (
        "inline-flex" in rendered
        and "gap-2" in rendered
        and "hidden" not in rendered
        and "bg-brand-primary-600" in rendered
    )

    # Config builder
    builder = TailwindConfigBuilder(reg)
    theme = builder.build_theme()
    checks["theme_colors"] = theme.colors.get("brand-primary-600") == "#2563EB"
    checks["theme_spacing"] = theme.spacing.get("space-4") == "1.0rem"
    checks["theme_radius"] = "radius-md" in theme.border_radius
    checks["theme_shadow"] = "shadow-md" in theme.box_shadow

    config_js = builder.render_config()
    checks["config_has_module_exports"] = "module.exports" in config_js
    checks["config_dark_class"] = "darkMode: 'class'" in config_js

    css_vars = builder.render_css_variables()
    checks["css_vars_has_root"] = ":root" in css_vars
    checks["css_vars_has_dark"] = ".dark" in css_vars
    checks["css_vars_color"] = "--color-brand-primary-600: #2563EB" in css_vars

    # Safelist
    sl = SafelistBuilder().add_many(["bg-success", "bg-danger", "text-warning"])
    checks["safelist_dedup"] = len(sl.to_list()) == 3

    return checks


__all__ = [
    "TAILWIND_STYLIST_VERSION", "TAILWIND_MIN_VERSION",
    "ROLE_TO_CONFIG_KEY",
    "ResolvedClass", "ClassResolver",
    "ClassList",
    "TailwindTheme", "TailwindConfigBuilder",
    "SafelistBuilder",
    "tailwind_stylist_sanity_check",
]
