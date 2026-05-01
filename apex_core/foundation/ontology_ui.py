"""
APEX FACTORY v6.0 - Foundation Extension
File: ontology_ui.py

Mục đích: Ontology UI/App — thay thế ontology XSMB khi hệ thống chuyển sang
          miền sản xuất Web/App. Giữ triết lý 3 tầng (nguyên tử → phân tử →
          hợp chất) như ontology cũ nhưng đổi vật chất.

Nguyên tắc bất biến áp dụng:
  NT3 - Traditional Culture   → thay bằng "Design System Integrity" (NT11)
  NT4 - Constrained Creativity → component CHỈ sinh từ catalog, không tự bịa
  NT11 - Design System Integrity (MỚI): mọi component phải tham chiếu token
  NT12 - Accessibility Non-Negotiable (MỚI): a11y_contract là bắt buộc
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

# ============================================================
# 0. VERSION + REGISTRY METADATA
# ============================================================

ONTOLOGY_UI_VERSION = "6.0.0"
ONTOLOGY_UI_SCHEMA = "apex.factory.ui/v6"


# ============================================================
# 1. ENUMS (đóng - mọi giá trị phải nằm trong đây)
# ============================================================

class ComponentCategory(str, Enum):
    """Atomic Design 5-layer (Brad Frost) + 2 extension layers."""
    ATOM = "atom"                # Button, Input, Icon, Label
    MOLECULE = "molecule"        # FormField, SearchBar, Card
    ORGANISM = "organism"        # Navbar, ProductGrid, CommentSection
    TEMPLATE = "template"        # PageLayout với slot trống
    PAGE = "page"                # Template đã bind dữ liệu
    PATTERN = "pattern"          # Giao diện lặp đa page (auth flow, checkout)
    LAYOUT = "layout"            # Grid, Stack, Cluster primitives


class RenderTarget(str, Enum):
    REACT = "react"
    REACT_NATIVE = "react_native"
    VUE = "vue"
    SVELTE = "svelte"
    FLUTTER = "flutter"
    SOLID = "solid"
    HTML_STATIC = "html_static"


class Breakpoint(str, Enum):
    """Chuẩn Tailwind để dễ emit."""
    XS = "xs"      # < 640
    SM = "sm"      # >= 640
    MD = "md"      # >= 768
    LG = "lg"      # >= 1024
    XL = "xl"      # >= 1280
    XXL = "2xl"    # >= 1536


class TokenRole(str, Enum):
    """Semantic role của token - không phụ thuộc giá trị cụ thể."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    SURFACE = "surface"
    SURFACE_ALT = "surface_alt"
    BACKGROUND = "background"
    TEXT = "text"
    TEXT_MUTED = "text_muted"
    BORDER = "border"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    INFO = "info"
    NEUTRAL = "neutral"


class ComponentState(str, Enum):
    DEFAULT = "default"
    HOVER = "hover"
    ACTIVE = "active"
    FOCUS = "focus"
    DISABLED = "disabled"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"
    SELECTED = "selected"


class A11yRole(str, Enum):
    """ARIA roles - subset phổ biến nhất."""
    BUTTON = "button"
    LINK = "link"
    NAVIGATION = "navigation"
    MAIN = "main"
    HEADER = "banner"
    FOOTER = "contentinfo"
    FORM = "form"
    DIALOG = "dialog"
    ALERT = "alert"
    TAB = "tab"
    TABLIST = "tablist"
    MENU = "menu"
    MENUITEM = "menuitem"
    LIST = "list"
    LISTITEM = "listitem"
    IMG = "img"
    HEADING = "heading"
    ARTICLE = "article"
    REGION = "region"
    NONE = "none"


# ============================================================
# 2. TẦNG NGUYÊN TỬ - DESIGN TOKENS (immutable, hashable)
# ============================================================

# Regex validators cho color string
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3}([0-9A-Fa-f]{2})?)?$")
RGB_COLOR_RE = re.compile(r"^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[\d.]+\s*)?\)$")


@dataclass(frozen=True)
class ColorToken:
    """1 màu trong design system. Giá trị cụ thể + role ngữ nghĩa."""
    token_id: str                   # "brand.primary.600"
    value: str                      # "#2563EB" hoặc "rgb(37,99,235)"
    role: TokenRole
    contrast_ratio_on_bg: float = 4.5   # AA default; AAA = 7.0
    dark_mode_variant: Optional[str] = None   # "#3B82F6"
    alpha: float = 1.0

    def __post_init__(self):
        if not (HEX_COLOR_RE.match(self.value) or RGB_COLOR_RE.match(self.value)):
            raise ValueError(f"Invalid color value: {self.value!r}")
        if not (0.0 <= self.alpha <= 1.0):
            raise ValueError(f"Alpha out of [0,1]: {self.alpha}")
        if self.contrast_ratio_on_bg < 3.0:
            raise ValueError(
                f"Contrast ratio < 3.0 vi phạm WCAG AA (NT12): {self.contrast_ratio_on_bg}"
            )


@dataclass(frozen=True)
class TypographyToken:
    """1 kiểu chữ trong design system."""
    token_id: str                   # "text.heading.h1"
    font_family: str                # "Inter, system-ui, sans-serif"
    font_size_rem: float            # 2.25
    font_weight: int                # 100..900
    line_height: float              # 1.2 (unitless multiplier)
    letter_spacing_em: float = 0.0
    font_style: str = "normal"      # normal | italic

    def __post_init__(self):
        if not (0.5 <= self.font_size_rem <= 12.0):
            raise ValueError(f"font_size_rem out of range: {self.font_size_rem}")
        if self.font_weight not in range(100, 1000, 100):
            raise ValueError(f"font_weight must be 100..900 step 100: {self.font_weight}")
        if not (0.8 <= self.line_height <= 3.0):
            raise ValueError(f"line_height unusual: {self.line_height}")


@dataclass(frozen=True)
class SpacingToken:
    """1 đơn vị spacing trong scale."""
    token_id: str                   # "space.4"
    scale_index: int                # 0, 1, 2, 4, 8 ...
    value_rem: float                # 1.0

    def __post_init__(self):
        if self.value_rem < 0:
            raise ValueError(f"Negative spacing: {self.value_rem}")


@dataclass(frozen=True)
class RadiusToken:
    token_id: str                   # "radius.md"
    value_rem: float                # 0.375


@dataclass(frozen=True)
class ShadowToken:
    """Box-shadow token. offset_x/y/blur/spread theo rem; color theo ref."""
    token_id: str                   # "shadow.md"
    offset_x_rem: float
    offset_y_rem: float
    blur_rem: float
    spread_rem: float
    color_ref: str                  # ColorToken.token_id
    inset: bool = False


@dataclass(frozen=True)
class MotionToken:
    """Animation/transition token."""
    token_id: str                   # "motion.fast"
    duration_ms: int                # 150
    easing: str                     # "cubic-bezier(0.4, 0, 0.2, 1)"
    property: str = "all"           # "opacity", "transform", ...

    def __post_init__(self):
        if not (0 <= self.duration_ms <= 5000):
            raise ValueError(f"duration_ms out of range: {self.duration_ms}")


@dataclass(frozen=True)
class IconToken:
    """SVG icon token."""
    token_id: str                   # "icon.chevron_down"
    view_box: str                   # "0 0 24 24"
    path_d: str                     # path data
    default_size_rem: float = 1.0


# Type alias cho mọi token
DesignToken = (
    ColorToken | TypographyToken | SpacingToken | RadiusToken
    | ShadowToken | MotionToken | IconToken
)


# ============================================================
# 3. TOKEN REGISTRY - nơi duy nhất tra token
# ============================================================

class TokenRegistry:
    """
    Registry tập trung cho toàn bộ design token của 1 project.
    Bất biến sau khi build xong để đảm bảo consistency (NT11).
    """

    def __init__(self) -> None:
        self._colors: Dict[str, ColorToken] = {}
        self._typography: Dict[str, TypographyToken] = {}
        self._spacing: Dict[str, SpacingToken] = {}
        self._radius: Dict[str, RadiusToken] = {}
        self._shadow: Dict[str, ShadowToken] = {}
        self._motion: Dict[str, MotionToken] = {}
        self._icons: Dict[str, IconToken] = {}
        self._frozen: bool = False

    def add(self, token: DesignToken) -> None:
        if self._frozen:
            raise RuntimeError("TokenRegistry is frozen (NT11 enforcement)")
        tid = token.token_id
        bucket = self._bucket_for(token)
        if tid in bucket:
            raise ValueError(f"Duplicate token_id: {tid}")
        bucket[tid] = token

    def _bucket_for(self, token: DesignToken) -> Dict[str, Any]:
        if isinstance(token, ColorToken):      return self._colors
        if isinstance(token, TypographyToken): return self._typography
        if isinstance(token, SpacingToken):    return self._spacing
        if isinstance(token, RadiusToken):     return self._radius
        if isinstance(token, ShadowToken):     return self._shadow
        if isinstance(token, MotionToken):     return self._motion
        if isinstance(token, IconToken):       return self._icons
        raise TypeError(f"Unknown token type: {type(token).__name__}")

    def get(self, token_id: str) -> Optional[DesignToken]:
        for bucket in (
            self._colors, self._typography, self._spacing,
            self._radius, self._shadow, self._motion, self._icons,
        ):
            if token_id in bucket:
                return bucket[token_id]
        return None

    def require(self, token_id: str) -> DesignToken:
        """Raise KeyError nếu không có - dùng để enforce NT11."""
        tok = self.get(token_id)
        if tok is None:
            raise KeyError(f"Token not in registry (NT11): {token_id}")
        return tok

    def freeze(self) -> None:
        """Khóa registry - không cho thêm token nữa."""
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def all_ids(self) -> FrozenSet[str]:
        ids: List[str] = []
        for bucket in (
            self._colors, self._typography, self._spacing,
            self._radius, self._shadow, self._motion, self._icons,
        ):
            ids.extend(bucket.keys())
        return frozenset(ids)

    def summary(self) -> Dict[str, int]:
        return {
            "colors": len(self._colors),
            "typography": len(self._typography),
            "spacing": len(self._spacing),
            "radius": len(self._radius),
            "shadow": len(self._shadow),
            "motion": len(self._motion),
            "icons": len(self._icons),
            "frozen": self._frozen,
        }

    def fingerprint(self) -> str:
        """Hash toàn registry để phát hiện drift."""
        payload = {
            "colors": sorted(self._colors.keys()),
            "typography": sorted(self._typography.keys()),
            "spacing": sorted(self._spacing.keys()),
            "radius": sorted(self._radius.keys()),
            "shadow": sorted(self._shadow.keys()),
            "motion": sorted(self._motion.keys()),
            "icons": sorted(self._icons.keys()),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()


# ============================================================
# 4. TẦNG PHÂN TỬ - COMPONENT SPEC
# ============================================================

@dataclass(frozen=True)
class PropSchema:
    """Schema đơn giản kiểu JSON Schema tối thiểu."""
    name: str
    type_hint: str                  # "string" | "number" | "boolean" | "enum" | "node" | "any"
    required: bool = False
    default: Any = None
    enum_values: Tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self):
        if self.type_hint == "enum" and not self.enum_values:
            raise ValueError(f"Prop {self.name}: enum type requires enum_values")


@dataclass(frozen=True)
class SlotSchema:
    """Mỗi component có thể có nhiều slot nhận children."""
    name: str                       # "default", "header", "footer"
    accepts_categories: Tuple[str, ...] = ()   # ComponentCategory values
    max_children: Optional[int] = None
    required: bool = False


@dataclass(frozen=True)
class A11yContract:
    """Hợp đồng accessibility BẮT BUỘC (NT12)."""
    role: A11yRole
    required_aria: Tuple[str, ...] = ()         # ("aria-label",)
    keyboard_map: Tuple[Tuple[str, str], ...] = ()  # (("Enter", "activate"),)
    focus_ring_required: bool = True
    screen_reader_notes: str = ""

    def validate(self) -> List[str]:
        """Return list of violations. Empty = compliant."""
        violations: List[str] = []
        if self.role in (A11yRole.BUTTON, A11yRole.LINK) and not self.keyboard_map:
            violations.append(f"{self.role.value} missing keyboard_map")
        if self.role == A11yRole.IMG and "aria-label" not in self.required_aria:
            violations.append("IMG must declare aria-label requirement")
        return violations


@dataclass(frozen=True)
class ResponsiveVariant:
    """Biến thể của component theo breakpoint."""
    breakpoint: Breakpoint
    override_props: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentSpec:
    """
    Phân tử của ontology UI. Tương đương '2-digit number' trong ontology XSMB cũ.
    """
    component_id: str               # "atom.button.primary"
    label: str                      # "Primary Button"
    category: ComponentCategory
    prop_schema: Tuple[PropSchema, ...]
    slots: Tuple[SlotSchema, ...]
    states: Tuple[ComponentState, ...]
    a11y: A11yContract
    design_tokens_used: Tuple[str, ...]         # token_ids (FK vào TokenRegistry)
    dependencies: Tuple[str, ...]               # component_ids (FK khác)
    render_targets: Tuple[RenderTarget, ...]
    responsive_variants: Tuple[ResponsiveVariant, ...] = ()
    tags: Tuple[str, ...] = ()                  # "hero", "cta", "pricing", ...
    version: str = "1.0.0"
    parse_confidence: float = 1.0               # kế thừa từ MethodSpec cũ
    source_type: str = "manual"                 # manual | imported | evolved
    content_hash: str = ""

    def __post_init__(self):
        if not re.match(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$", self.component_id):
            raise ValueError(
                f"component_id must be dotted.snake_case: {self.component_id!r}"
            )
        if not (0.0 <= self.parse_confidence <= 1.0):
            raise ValueError(f"parse_confidence out of [0,1]: {self.parse_confidence}")
        # NT12: a11y_contract phải pass validate
        a11y_violations = self.a11y.validate()
        if a11y_violations:
            raise ValueError(
                f"Component {self.component_id} vi phạm NT12: {a11y_violations}"
            )
        # Compute content hash if not provided
        if not self.content_hash:
            object.__setattr__(self, "content_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        payload = {
            "component_id": self.component_id,
            "category": self.category.value,
            "props": [asdict(p) for p in self.prop_schema],
            "slots": [asdict(s) for s in self.slots],
            "states": [s.value for s in self.states],
            "tokens": list(self.design_tokens_used),
            "deps": list(self.dependencies),
            "targets": [t.value for t in self.render_targets],
            "version": self.version,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def validate_against_registry(self, registry: TokenRegistry) -> List[str]:
        """NT11: mọi token dùng phải có trong registry."""
        missing: List[str] = []
        for tid in self.design_tokens_used:
            if registry.get(tid) is None:
                missing.append(tid)
        return [f"Token not in registry: {m}" for m in missing]

    def supports_target(self, target: RenderTarget) -> bool:
        return target in self.render_targets

    def get_prop(self, name: str) -> Optional[PropSchema]:
        for p in self.prop_schema:
            if p.name == name:
                return p
        return None

    def get_slot(self, name: str) -> Optional[SlotSchema]:
        for s in self.slots:
            if s.name == name:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "label": self.label,
            "category": self.category.value,
            "prop_schema": [asdict(p) for p in self.prop_schema],
            "slots": [asdict(s) for s in self.slots],
            "states": [s.value for s in self.states],
            "a11y": {
                "role": self.a11y.role.value,
                "required_aria": list(self.a11y.required_aria),
                "keyboard_map": [list(km) for km in self.a11y.keyboard_map],
                "focus_ring_required": self.a11y.focus_ring_required,
                "screen_reader_notes": self.a11y.screen_reader_notes,
            },
            "design_tokens_used": list(self.design_tokens_used),
            "dependencies": list(self.dependencies),
            "render_targets": [t.value for t in self.render_targets],
            "responsive_variants": [
                {
                    "breakpoint": rv.breakpoint.value,
                    "override_props": dict(rv.override_props),
                }
                for rv in self.responsive_variants
            ],
            "tags": list(self.tags),
            "version": self.version,
            "parse_confidence": self.parse_confidence,
            "source_type": self.source_type,
            "content_hash": self.content_hash,
        }


# ============================================================
# 5. COMPONENT CATALOG - vault của ComponentSpec
# ============================================================

class ComponentCatalog:
    """
    Catalog các ComponentSpec. Thay thế vai trò của Method Vault cũ
    khi hệ thống pivot sang sản xuất UI.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, ComponentSpec] = {}
        self._by_category: Dict[ComponentCategory, List[str]] = {
            cat: [] for cat in ComponentCategory
        }
        self._by_tag: Dict[str, List[str]] = {}

    def register(self, spec: ComponentSpec) -> None:
        if spec.component_id in self._by_id:
            raise ValueError(f"Component đã tồn tại: {spec.component_id}")
        self._by_id[spec.component_id] = spec
        self._by_category[spec.category].append(spec.component_id)
        for tag in spec.tags:
            self._by_tag.setdefault(tag, []).append(spec.component_id)

    def get(self, component_id: str) -> Optional[ComponentSpec]:
        return self._by_id.get(component_id)

    def require(self, component_id: str) -> ComponentSpec:
        spec = self.get(component_id)
        if spec is None:
            raise KeyError(f"Component not in catalog: {component_id}")
        return spec

    def search_by_category(self, category: ComponentCategory) -> List[ComponentSpec]:
        return [self._by_id[cid] for cid in self._by_category.get(category, [])]

    def search_by_tag(self, tag: str) -> List[ComponentSpec]:
        return [self._by_id[cid] for cid in self._by_tag.get(tag, [])]

    def search_by_target(self, target: RenderTarget) -> List[ComponentSpec]:
        return [s for s in self._by_id.values() if s.supports_target(target)]

    def all(self) -> List[ComponentSpec]:
        return list(self._by_id.values())

    def size(self) -> int:
        return len(self._by_id)

    def validate_all(self, registry: TokenRegistry) -> Dict[str, List[str]]:
        """Return {component_id: [violations]} - empty dict = tất cả OK."""
        violations: Dict[str, List[str]] = {}
        for cid, spec in self._by_id.items():
            v = spec.validate_against_registry(registry)
            # Kiểm thêm dependency FK
            for dep_id in spec.dependencies:
                if dep_id not in self._by_id:
                    v.append(f"Dependency not in catalog: {dep_id}")
            if v:
                violations[cid] = v
        return violations

    def resolve_dependency_order(self) -> List[str]:
        """Topological sort - component có ít dependency đi trước."""
        visited: Dict[str, int] = {}   # 0=unseen, 1=in-progress, 2=done
        order: List[str] = []

        def visit(cid: str) -> None:
            state = visited.get(cid, 0)
            if state == 2:
                return
            if state == 1:
                raise ValueError(f"Dependency cycle detected at: {cid}")
            visited[cid] = 1
            spec = self._by_id.get(cid)
            if spec is not None:
                for dep in spec.dependencies:
                    visit(dep)
            visited[cid] = 2
            order.append(cid)

        for cid in self._by_id:
            visit(cid)
        return order

    def fingerprint(self) -> str:
        hashes = sorted(s.content_hash for s in self._by_id.values())
        return hashlib.sha256(
            json.dumps(hashes).encode("utf-8")
        ).hexdigest()


# ============================================================
# 6. SANITY CHECK
# ============================================================

def ontology_ui_sanity_check() -> Dict[str, bool]:
    """Self-test - gọi khi boot ApexFactory."""
    checks: Dict[str, bool] = {}

    # TokenRegistry basic ops
    try:
        reg = TokenRegistry()
        reg.add(ColorToken("c.primary", "#2563EB", TokenRole.PRIMARY))
        reg.add(SpacingToken("s.4", 4, 1.0))
        reg.freeze()
        checks["token_registry_freeze"] = reg.is_frozen
        try:
            reg.add(SpacingToken("s.8", 8, 2.0))
            checks["token_registry_freeze_enforced"] = False
        except RuntimeError:
            checks["token_registry_freeze_enforced"] = True
    except Exception:
        checks["token_registry_basic"] = False
    else:
        checks["token_registry_basic"] = True

    # ComponentSpec construction + a11y enforcement
    try:
        spec = ComponentSpec(
            component_id="atom.button.primary",
            label="Primary Button",
            category=ComponentCategory.ATOM,
            prop_schema=(
                PropSchema("children", "node", required=True),
                PropSchema("onClick", "any"),
            ),
            slots=(),
            states=(ComponentState.DEFAULT, ComponentState.HOVER, ComponentState.DISABLED),
            a11y=A11yContract(
                role=A11yRole.BUTTON,
                keyboard_map=(("Enter", "activate"), ("Space", "activate")),
            ),
            design_tokens_used=("c.primary",),
            dependencies=(),
            render_targets=(RenderTarget.REACT, RenderTarget.VUE),
        )
        checks["component_spec_build"] = spec.content_hash != ""
    except Exception:
        checks["component_spec_build"] = False

    # A11y violation enforcement (NT12)
    try:
        ComponentSpec(
            component_id="atom.img.bare",
            label="Bare Image",
            category=ComponentCategory.ATOM,
            prop_schema=(PropSchema("src", "string", required=True),),
            slots=(),
            states=(ComponentState.DEFAULT,),
            a11y=A11yContract(role=A11yRole.IMG),   # Thiếu aria-label → must raise
            design_tokens_used=(),
            dependencies=(),
            render_targets=(RenderTarget.REACT,),
        )
        checks["a11y_violation_blocked"] = False
    except ValueError:
        checks["a11y_violation_blocked"] = True

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    # Meta
    "ONTOLOGY_UI_VERSION",
    "ONTOLOGY_UI_SCHEMA",
    # Enums
    "ComponentCategory",
    "RenderTarget",
    "Breakpoint",
    "TokenRole",
    "ComponentState",
    "A11yRole",
    # Tokens
    "ColorToken",
    "TypographyToken",
    "SpacingToken",
    "RadiusToken",
    "ShadowToken",
    "MotionToken",
    "IconToken",
    "DesignToken",
    # Registry
    "TokenRegistry",
    # Component
    "PropSchema",
    "SlotSchema",
    "A11yContract",
    "ResponsiveVariant",
    "ComponentSpec",
    "ComponentCatalog",
    # Sanity
    "ontology_ui_sanity_check",
]
