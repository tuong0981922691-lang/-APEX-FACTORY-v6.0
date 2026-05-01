"""
APEX FACTORY v6.0 - Emitter Layer
File: ast_backbone.py

Mục đích: AST xương sống chung cho mọi emitter (React/Vue/Svelte...).
    Mọi emitter sinh AST trước, pretty-print sau. Lý do:
      - Dễ diff/patch ở Phase 4 (Forge)
      - Dễ test: so sánh AST thay vì so sánh string
      - Dễ hot-inject: tiêm node vào AST an toàn hơn string replace

Triết lý: AST ở đây không phải AST chuẩn TS/Babel đầy đủ. Đây là AST
          "tác nghiệp" - đủ để sinh component files, không cần parse lại.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# ============================================================
# 0. VERSION + CONSTANTS
# ============================================================

AST_BACKBONE_VERSION = "6.0.0"

INDENT = "  "           # 2 spaces (chuẩn Prettier/Airbnb TS)
MAX_LINE_LENGTH = 100   # soft wrap hint


# ============================================================
# 1. IMPORT SPEC
# ============================================================

@dataclass(frozen=True)
class ImportSpec:
    """1 dòng import. Hỗ trợ: default, named, side-effect, namespace."""
    module: str                             # "react" | "./Button" | ...
    default_name: Optional[str] = None      # `import X from ...`
    named_imports: Tuple[str, ...] = ()     # `import { A, B } from ...`
    namespace_name: Optional[str] = None    # `import * as Ns from ...`
    type_only: bool = False                 # `import type { ... }`
    side_effect_only: bool = False          # `import "./styles.css"`

    def __post_init__(self):
        if self.side_effect_only and (
            self.default_name or self.named_imports or self.namespace_name
        ):
            raise ValueError("side_effect_only import cannot have any names")

    def render(self) -> str:
        if self.side_effect_only:
            return f'import "{self.module}";'

        parts: List[str] = []
        if self.default_name:
            parts.append(self.default_name)
        if self.namespace_name:
            parts.append(f"* as {self.namespace_name}")
        if self.named_imports:
            parts.append("{ " + ", ".join(self.named_imports) + " }")

        if not parts:
            return ""
        prefix = "import type" if self.type_only else "import"
        body = ", ".join(parts)
        return f'{prefix} {body} from "{self.module}";'


def merge_imports(imports: Sequence[ImportSpec]) -> List[ImportSpec]:
    """Gom các import cùng module + cùng type_only."""
    buckets: Dict[Tuple[str, bool], Dict[str, Any]] = {}
    side_effects: List[ImportSpec] = []

    for imp in imports:
        if imp.side_effect_only:
            side_effects.append(imp)
            continue
        key = (imp.module, imp.type_only)
        if key not in buckets:
            buckets[key] = {
                "default": imp.default_name,
                "namespace": imp.namespace_name,
                "named": set(imp.named_imports),
            }
        else:
            b = buckets[key]
            if imp.default_name and not b["default"]:
                b["default"] = imp.default_name
            if imp.namespace_name and not b["namespace"]:
                b["namespace"] = imp.namespace_name
            b["named"].update(imp.named_imports)

    merged: List[ImportSpec] = []
    for (module, type_only), b in sorted(buckets.items()):
        merged.append(ImportSpec(
            module=module,
            default_name=b["default"],
            named_imports=tuple(sorted(b["named"])),
            namespace_name=b["namespace"],
            type_only=type_only,
        ))
    # Side-effect sau cùng
    merged.extend(side_effects)
    return merged


# ============================================================
# 2. JSX / TEMPLATE NODES
# ============================================================

class NodeKind(str, Enum):
    ELEMENT = "element"
    FRAGMENT = "fragment"
    TEXT = "text"
    EXPRESSION = "expression"
    COMMENT = "comment"


@dataclass(frozen=True)
class JSXAttribute:
    """
    Attribute trên JSXElement.
    Value có thể là string literal, expression, hoặc boolean shorthand.
    """
    name: str                           # "className" | "onClick" | ...
    value: Any = None                   # None → shorthand `<Btn disabled />`
    is_expression: bool = False         # True → `{expr}`; False → `"literal"`
    is_spread: bool = False              # {...props}

    def render(self) -> str:
        if self.is_spread:
            raw = str(self.value) if self.value is not None else ""
            return f"{{...{raw}}}"
        if self.value is None:
            return self.name
        if self.is_expression:
            return f"{self.name}={{{self.value}}}"
        # string literal - escape double quotes
        escaped = str(self.value).replace('"', '\\"')
        return f'{self.name}="{escaped}"'


@dataclass
class JSXNode:
    """Base union. Dùng kind + fields linh hoạt."""
    kind: NodeKind
    # ELEMENT / FRAGMENT
    tag: Optional[str] = None                       # "div" | "Button" | ...
    attributes: List[JSXAttribute] = field(default_factory=list)
    children: List["JSXNode"] = field(default_factory=list)
    self_closing_hint: bool = False
    # TEXT / EXPRESSION / COMMENT
    text: Optional[str] = None

    # --- Convenience constructors ---
    @classmethod
    def element(
        cls,
        tag: str,
        *,
        attributes: Optional[Sequence[JSXAttribute]] = None,
        children: Optional[Sequence["JSXNode"]] = None,
        self_closing: bool = False,
    ) -> "JSXNode":
        return cls(
            kind=NodeKind.ELEMENT,
            tag=tag,
            attributes=list(attributes or []),
            children=list(children or []),
            self_closing_hint=self_closing,
        )

    @classmethod
    def fragment(cls, children: Sequence["JSXNode"]) -> "JSXNode":
        return cls(kind=NodeKind.FRAGMENT, children=list(children))

    @classmethod
    def text_node(cls, text: str) -> "JSXNode":
        return cls(kind=NodeKind.TEXT, text=text)

    @classmethod
    def expression(cls, code: str) -> "JSXNode":
        return cls(kind=NodeKind.EXPRESSION, text=code)

    @classmethod
    def comment(cls, text: str) -> "JSXNode":
        return cls(kind=NodeKind.COMMENT, text=text)

    def render(self, indent_level: int = 0) -> str:
        pad = INDENT * indent_level

        if self.kind == NodeKind.TEXT:
            return pad + self._escape_text_child(self.text or "")

        if self.kind == NodeKind.EXPRESSION:
            return f"{pad}{{{self.text or ''}}}"

        if self.kind == NodeKind.COMMENT:
            return f"{pad}{{/* {self.text or ''} */}}"

        if self.kind == NodeKind.FRAGMENT:
            if not self.children:
                return f"{pad}<></>"
            parts = [f"{pad}<>"]
            for child in self.children:
                parts.append(child.render(indent_level + 1))
            parts.append(f"{pad}</>")
            return "\n".join(parts)

        # ELEMENT
        assert self.tag, "ELEMENT requires tag"
        attr_str = self._render_attrs(indent_level)

        is_empty = not self.children
        should_self_close = self.self_closing_hint or is_empty

        if should_self_close:
            sep = " " if attr_str else ""
            return f"{pad}<{self.tag}{sep}{attr_str} />" if attr_str else f"{pad}<{self.tag} />"

        open_tag = f"<{self.tag}{' ' + attr_str if attr_str else ''}>"
        close_tag = f"</{self.tag}>"

        # Compact single-child text
        if (
            len(self.children) == 1
            and self.children[0].kind == NodeKind.TEXT
            and self.children[0].text
            and "\n" not in self.children[0].text
        ):
            return f"{pad}{open_tag}{self.children[0].text}{close_tag}"

        lines = [f"{pad}{open_tag}"]
        for child in self.children:
            lines.append(child.render(indent_level + 1))
        lines.append(f"{pad}{close_tag}")
        return "\n".join(lines)

    def _render_attrs(self, indent_level: int) -> str:
        if not self.attributes:
            return ""
        rendered = [a.render() for a in self.attributes]
        single_line = " ".join(rendered)
        # Nếu quá dài → multi-line
        if len(single_line) <= MAX_LINE_LENGTH - (indent_level * len(INDENT)):
            return single_line
        inner_pad = INDENT * (indent_level + 1)
        return "\n".join(f"{inner_pad}{a}" for a in rendered).lstrip()

    @staticmethod
    def _escape_text_child(text: str) -> str:
        """Escape < > { } trong text JSX."""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("{", "&#123;")
                .replace("}", "&#125;")
        )


# ============================================================
# 3. TYPESCRIPT TYPE NODES
# ============================================================

@dataclass(frozen=True)
class TSType:
    """
    Biểu diễn TS type dưới dạng string literal (đã render).
    Có thể là union, intersection, generic, array...
    VD: TSType("string"), TSType("React.FC<ButtonProps>")
    """
    text: str

    def render(self) -> str:
        return self.text


TS_STRING = TSType("string")
TS_NUMBER = TSType("number")
TS_BOOLEAN = TSType("boolean")
TS_UNKNOWN = TSType("unknown")
TS_ANY = TSType("any")
TS_VOID = TSType("void")
TS_REACT_NODE = TSType("React.ReactNode")


@dataclass(frozen=True)
class TSProperty:
    name: str
    type_: TSType
    optional: bool = False
    readonly: bool = False
    docstring: str = ""

    def render(self) -> str:
        lines: List[str] = []
        if self.docstring:
            lines.append(f"  /** {self.docstring} */")
        prefix = "readonly " if self.readonly else ""
        suffix = "?" if self.optional else ""
        lines.append(f"  {prefix}{self.name}{suffix}: {self.type_.render()};")
        return "\n".join(lines)


@dataclass
class TSInterface:
    name: str
    properties: List[TSProperty] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    exported: bool = True

    def render(self) -> str:
        export = "export " if self.exported else ""
        ext = f" extends {', '.join(self.extends)}" if self.extends else ""
        lines = [f"{export}interface {self.name}{ext} {{"]
        for prop in self.properties:
            lines.append(prop.render())
        lines.append("}")
        return "\n".join(lines)


@dataclass
class TSTypeAlias:
    name: str
    type_: TSType
    exported: bool = True

    def render(self) -> str:
        export = "export " if self.exported else ""
        return f"{export}type {self.name} = {self.type_.render()};"


# ============================================================
# 4. FUNCTION / CONST DECLARATIONS
# ============================================================

@dataclass(frozen=True)
class FunctionParam:
    name: str
    type_: Optional[TSType] = None
    default: Optional[str] = None

    def render(self) -> str:
        t = f": {self.type_.render()}" if self.type_ else ""
        d = f" = {self.default}" if self.default else ""
        return f"{self.name}{t}{d}"


@dataclass
class FunctionDeclaration:
    """
    Function/arrow function declaration.
    Body hoặc là list of statement strings, hoặc là 1 JSX return.
    """
    name: str
    params: List[FunctionParam] = field(default_factory=list)
    return_type: Optional[TSType] = None
    body_statements: List[str] = field(default_factory=list)
    return_jsx: Optional[JSXNode] = None
    exported: bool = True
    is_default_export: bool = False
    is_arrow: bool = True
    is_async: bool = False

    def render(self) -> str:
        export = ""
        if self.exported:
            export = "export default " if self.is_default_export else "export "

        params_str = ", ".join(p.render() for p in self.params)
        ret_str = f": {self.return_type.render()}" if self.return_type else ""
        async_prefix = "async " if self.is_async else ""

        if self.is_arrow:
            # const Name = (params): ret => { body; return (...); };
            lines = [f"{export}const {self.name} = {async_prefix}({params_str}){ret_str} => {{"]
        else:
            # function Name(params): ret { body }
            lines = [
                f"{export}{async_prefix}function {self.name}({params_str}){ret_str} {{"
            ]

        for stmt in self.body_statements:
            lines.append(f"{INDENT}{stmt}")

        if self.return_jsx is not None:
            lines.append(f"{INDENT}return (")
            lines.append(self.return_jsx.render(indent_level=2))
            lines.append(f"{INDENT});")
        elif not self.body_statements:
            lines.append(f"{INDENT}return null;")

        lines.append("};" if self.is_arrow else "}")
        return "\n".join(lines)


@dataclass
class ConstDeclaration:
    name: str
    value_expr: str                         # raw JS/TS expression
    type_: Optional[TSType] = None
    exported: bool = False

    def render(self) -> str:
        export = "export " if self.exported else ""
        t = f": {self.type_.render()}" if self.type_ else ""
        return f"{export}const {self.name}{t} = {self.value_expr};"


# ============================================================
# 5. FILE MODULE (đơn vị output của emitter)
# ============================================================

TopLevelNode = Union[TSInterface, TSTypeAlias, FunctionDeclaration, ConstDeclaration, str]


@dataclass
class FileModule:
    """1 file .tsx/.ts/.vue. Emitter trả về FileModule rồi caller ghi xuống disk."""
    file_path: str                          # "src/components/Button.tsx"
    language: str                           # "typescript_react" | "typescript" | "vue"
    imports: List[ImportSpec] = field(default_factory=list)
    top_level: List[TopLevelNode] = field(default_factory=list)
    header_comment: str = ""
    trailing_newline: bool = True

    def add_import(self, imp: ImportSpec) -> None:
        self.imports.append(imp)

    def add_top_level(self, node: TopLevelNode) -> None:
        self.top_level.append(node)

    def render(self) -> str:
        blocks: List[str] = []

        if self.header_comment:
            blocks.append(self._render_header_comment())

        if self.imports:
            merged = merge_imports(self.imports)
            import_lines = [imp.render() for imp in merged if imp.render()]
            if import_lines:
                blocks.append("\n".join(import_lines))

        for node in self.top_level:
            if isinstance(node, str):
                blocks.append(node)
            else:
                blocks.append(node.render())

        rendered = "\n\n".join(blocks)
        if self.trailing_newline and not rendered.endswith("\n"):
            rendered += "\n"
        return rendered

    def _render_header_comment(self) -> str:
        lines = self.header_comment.strip().splitlines()
        wrapped = ["/**"] + [f" * {ln}" for ln in lines] + [" */"]
        return "\n".join(wrapped)


# ============================================================
# 6. CODE EMITTER BASE
# ============================================================

class CodeEmitterError(Exception):
    pass


class CodeEmitter:
    """
    Base class cho React/Vue/Svelte emitter.
    Subclass phải implement emit_graph(graph) -> List[FileModule].
    """
    EMITTER_ID: str = "base"
    TARGET_LANGUAGE: str = "typescript_react"

    def emit_graph(self, graph: Any) -> List[FileModule]:
        raise NotImplementedError


# ============================================================
# 7. HELPERS: identifier sanitization
# ============================================================

_IDENT_STRIP = re.compile(r"[^A-Za-z0-9_]")
_LEADING_DIGIT = re.compile(r"^\d")


def to_pascal_case(s: str) -> str:
    """
    'organism.navbar.default' → 'OrganismNavbarDefault'
    'atom.button.primary'    → 'AtomButtonPrimary'
    """
    if not s:
        return "Unnamed"
    parts = re.split(r"[^A-Za-z0-9]+", s)
    parts = [p for p in parts if p]
    camel = "".join(p[:1].upper() + p[1:] for p in parts)
    if _LEADING_DIGIT.match(camel):
        camel = f"C{camel}"
    camel = _IDENT_STRIP.sub("", camel)
    return camel or "Unnamed"


def to_camel_case(s: str) -> str:
    pascal = to_pascal_case(s)
    if not pascal:
        return "unnamed"
    return pascal[0].lower() + pascal[1:]


def sanitize_prop_name(name: str) -> str:
    """Prop name cho JSX: giữ camelCase, strip ký tự đặc biệt."""
    clean = _IDENT_STRIP.sub("", name)
    if not clean:
        return "prop"
    if _LEADING_DIGIT.match(clean):
        clean = f"p{clean}"
    return clean[0].lower() + clean[1:]


def to_jsx_value(value: Any) -> Tuple[str, bool]:
    """
    Convert Python value → (rendered_value, is_expression).
    - str → ("text", False)  — string literal
    - bool/int/float/None → JS literal wrapped in expression
    - dict/list → JSON expression
    """
    if isinstance(value, str):
        return value, False
    if value is None:
        return "null", True
    if isinstance(value, bool):
        return "true" if value else "false", True
    if isinstance(value, (int, float)):
        return str(value), True
    # dict/list → JSON
    try:
        return json.dumps(value, ensure_ascii=False), True
    except Exception:
        return "null", True


# ============================================================
# 8. SANITY CHECK
# ============================================================

def ast_backbone_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    # ImportSpec
    imp = ImportSpec(module="react", default_name="React", named_imports=("useState",))
    checks["import_render"] = imp.render() == 'import React, { useState } from "react";'

    # Import merge
    merged = merge_imports([
        ImportSpec(module="react", default_name="React"),
        ImportSpec(module="react", named_imports=("useState",)),
        ImportSpec(module="react", named_imports=("useEffect",)),
    ])
    checks["merge_imports"] = (
        len(merged) == 1
        and merged[0].default_name == "React"
        and set(merged[0].named_imports) == {"useState", "useEffect"}
    )

    # JSX element
    btn = JSXNode.element(
        "button",
        attributes=[
            JSXAttribute("className", "btn btn-primary"),
            JSXAttribute("onClick", "handleClick", is_expression=True),
        ],
        children=[JSXNode.text_node("Click me")],
    )
    rendered = btn.render()
    checks["jsx_element_ok"] = (
        "className=\"btn btn-primary\"" in rendered
        and "onClick={handleClick}" in rendered
        and "Click me" in rendered
    )

    # Self-closing
    img = JSXNode.element(
        "img",
        attributes=[JSXAttribute("src", "/logo.png"), JSXAttribute("alt", "Logo")],
        self_closing=True,
    )
    checks["jsx_self_close"] = img.render().endswith("/>")

    # TSInterface
    iface = TSInterface(
        name="ButtonProps",
        properties=[
            TSProperty("label", TS_STRING, optional=False),
            TSProperty("onClick", TSType("() => void"), optional=True),
        ],
    )
    iface_text = iface.render()
    checks["ts_interface_ok"] = (
        "export interface ButtonProps" in iface_text
        and "label: string;" in iface_text
        and "onClick?: () => void;" in iface_text
    )

    # FunctionDeclaration
    fn = FunctionDeclaration(
        name="Button",
        params=[FunctionParam("props", TSType("ButtonProps"))],
        return_type=TSType("JSX.Element"),
        return_jsx=btn,
        is_default_export=True,
    )
    fn_text = fn.render()
    checks["fn_decl_ok"] = "export default const Button" in fn_text and "return (" in fn_text

    # FileModule
    mod = FileModule(
        file_path="src/Button.tsx",
        language="typescript_react",
        imports=[ImportSpec(module="react", default_name="React")],
        top_level=[iface, fn],
        header_comment="Button component\nAuto-generated",
    )
    mod_text = mod.render()
    checks["file_module_ok"] = (
        "/**" in mod_text
        and "import React" in mod_text
        and "interface ButtonProps" in mod_text
        and "const Button" in mod_text
    )

    # Case sanitizers
    checks["pascal_case"] = to_pascal_case("organism.navbar.default") == "OrganismNavbarDefault"
    checks["camel_case"] = to_camel_case("atom.button.primary") == "atomButtonPrimary"
    checks["pascal_leading_digit"] = to_pascal_case("1st_section") == "C1stSection"

    return checks


__all__ = [
    "AST_BACKBONE_VERSION",
    "INDENT", "MAX_LINE_LENGTH",
    "ImportSpec", "merge_imports",
    "NodeKind", "JSXAttribute", "JSXNode",
    "TSType", "TSProperty", "TSInterface", "TSTypeAlias",
    "TS_STRING", "TS_NUMBER", "TS_BOOLEAN", "TS_UNKNOWN", "TS_ANY", "TS_VOID", "TS_REACT_NODE",
    "FunctionParam", "FunctionDeclaration", "ConstDeclaration",
    "FileModule", "CodeEmitter", "CodeEmitterError",
    "to_pascal_case", "to_camel_case", "sanitize_prop_name", "to_jsx_value",
    "ast_backbone_sanity_check",
]
