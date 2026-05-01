"""
APEX FACTORY v6.0 - Emitter Layer
File: vue_emitter.py

Mục đích: Target phụ - sinh Vue 3 SFC (.vue) từ DesignGraph.
    Tại sao nhẹ hơn React: Vue SFC dùng template HTML-like (không cần JSX AST),
    script-setup là TypeScript đơn giản, style scoped có sẵn.

    Không share ast_backbone (JSX-specific) - dùng string-builder trực tiếp.

Lưu ý: Đây là emitter PHỤ, bật khi brief.constraints["render_target"] = "vue".
      Target chính của Factory v6 vẫn là React (chốt với C2).
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional, Set

from apex_core.emitters.ast_backbone import (
    CodeEmitter,
    FileModule,
    to_camel_case,
    to_pascal_case,
)
from apex_core.emitters.react_emitter import (
    HTML_TAGS,
    EmitConfig,
    EmitResult,
)
from apex_core.emitters.tailwind_stylist import (
    ClassList,
    TailwindConfigBuilder,
)
from apex_core.foundation.ontology_ui import (
    ComponentCatalog,
    ComponentSpec,
    PropSchema,
    RenderTarget,
    TokenRegistry,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.foundation.ui_ir import (
    DataSourceKind,
    DesignGraph,
    DesignNode,
)

# ============================================================
# 0. VERSION
# ============================================================

VUE_EMITTER_VERSION = "6.0.0"

VUE_VERSION = "^3.4.0"
VITE_PLUGIN_VUE_VERSION = "^5.0.0"


# ============================================================
# 1. HELPERS (TypeScript type from PropSchema - mini copy)
# ============================================================

def _prop_to_ts(prop: PropSchema) -> str:
    t = prop.type_hint
    if t == "string": return "string"
    if t == "number": return "number"
    if t == "boolean": return "boolean"
    if t == "node":   return "unknown"     # Vue slot - không cần prop type
    if t == "any":    return "any"
    if t == "enum" and prop.enum_values:
        return " | ".join(f'"{v}"' for v in prop.enum_values)
    return "unknown"


# ============================================================
# 2. VUE EMITTER
# ============================================================

class VueEmitter(CodeEmitter):
    EMITTER_ID = "vue"
    TARGET_LANGUAGE = "vue"

    def __init__(
        self,
        catalog: ComponentCatalog,
        token_registry: TokenRegistry,
        config: Optional[EmitConfig] = None,
    ):
        self.catalog = catalog
        self.registry = token_registry
        self.config = config or EmitConfig()
        self._warnings: List[str] = []

    @enforce_principle_v6(PrincipleV6.NT11_DESIGN_SYSTEM_INTEGRITY)
    def emit_graph(self, graph: DesignGraph) -> EmitResult:
        self._warnings = []
        if graph.target != RenderTarget.VUE:
            self._warnings.append(
                f"Graph target={graph.target.value} nhưng dùng VueEmitter"
            )

        files: List[FileModule] = []
        used_ids: Set[str] = {n.component_id for n in graph.nodes.values()}

        # 1. Component SFC files
        for cid in sorted(used_ids):
            if cid in HTML_TAGS:
                continue
            file_mod = self._build_sfc_file(cid)
            if file_mod:
                files.append(file_mod)

        # 2. App.vue (root)
        files.append(self._build_app_sfc(graph, used_ids))

        # 3. main.ts (entry)
        files.append(self._build_main_ts())

        # 4. Scaffold
        scaffold: Dict[str, str] = {}
        if self.config.generate_scaffold:
            tw_builder = TailwindConfigBuilder(self.registry)
            scaffold["tailwind.config.js"] = tw_builder.render_config()
            scaffold["postcss.config.js"] = (
                "module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };\n"
            )
            scaffold[f"{self.config.target_src_dir}/{self.config.styles_subdir}/tokens.css"] = (
                tw_builder.render_css_variables()
                + "\n@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"
            )
            scaffold["vite.config.ts"] = self._render_vite_config()
            scaffold["tsconfig.json"] = self._render_tsconfig()
            scaffold["package.json"] = self._render_package_json()
            scaffold["index.html"] = self._render_index_html()

        stats = {
            "component_count": len(used_ids),
            "file_count": len(files),
            "placeholder_count": sum(
                1 for n in graph.nodes.values()
                if n.component_id.startswith("placeholder.")
            ),
            "node_count": len(graph.nodes),
        }

        return EmitResult(
            files=files,
            entry_file_path=f"{self.config.target_src_dir}/main.ts",
            scaffold_files=scaffold,
            warnings=list(self._warnings),
            stats=stats,
        )

    # ============================================================
    # 3. SFC BUILDING
    # ============================================================

    def _build_sfc_file(self, component_id: str) -> Optional[FileModule]:
        comp_name = to_pascal_case(component_id)
        is_placeholder = component_id.startswith("placeholder.")
        spec = self.catalog.get(component_id)
        file_path = (
            f"{self.config.target_src_dir}/"
            f"{self.config.components_subdir}/"
            f"{comp_name}/{comp_name}.vue"
        )
        content = self._render_sfc_content(
            component_name=comp_name,
            component_id=component_id,
            spec=spec,
            is_placeholder=is_placeholder,
        )
        # Dùng FileModule ở mode "raw string" (top_level = [raw_str])
        mod = FileModule(file_path=file_path, language="vue")
        mod.top_level.append(content)
        mod.imports = []
        mod.trailing_newline = False
        return mod

    def _render_sfc_content(
        self,
        component_name: str,
        component_id: str,
        spec: Optional[ComponentSpec],
        is_placeholder: bool,
    ) -> str:
        # 1. Script setup
        script_lines: List[str] = [
            "<script setup lang=\"ts\">",
            f"// Auto-generated by APEX FACTORY v6.0 - VueEmitter {VUE_EMITTER_VERSION}",
            f"// Component: {component_id}",
        ]
        if is_placeholder:
            script_lines.append("// !!! PLACEHOLDER - fill trước khi publish.")

        # Props interface
        if spec is None:
            script_lines.append("interface Props { className?: string }")
        else:
            parts: List[str] = []
            for p in spec.prop_schema:
                optional = "" if p.required else "?"
                parts.append(f"  {p.name}{optional}: {_prop_to_ts(p)}")
            parts.append("  className?: string")
            script_lines.append("interface Props {")
            script_lines.extend(parts)
            script_lines.append("}")

        script_lines.append("const props = defineProps<Props>();")
        script_lines.append("</script>")

        # 2. Template
        tag = self._default_tag(spec)
        aria_role = (
            spec.a11y.role.value
            if spec and spec.a11y.role.value not in ("none", "heading")
            else None
        )
        template_lines = ["<template>"]
        attrs: List[str] = []
        if aria_role:
            attrs.append(f'role="{aria_role}"')
        attrs.append(':class="props.className"')
        template_lines.append(f"  <{tag} {' '.join(attrs)}>")
        template_lines.append("    <slot />")
        if is_placeholder:
            template_lines.append(
                f"    <!-- TODO fill placeholder: {component_id} -->"
            )
        template_lines.append(f"  </{tag}>")
        template_lines.append("</template>")

        # 3. Style scoped (placeholder cho custom CSS nếu cần)
        style_lines = [
            "<style scoped>",
            f"/* Component {component_name} - styles override here if needed */",
            "</style>",
        ]

        return "\n".join(script_lines + [""] + template_lines + [""] + style_lines) + "\n"

    def _default_tag(self, spec: Optional[ComponentSpec]) -> str:
        if spec is None:
            return "div"
        return {
            "navigation": "nav",
            "banner":     "header",
            "contentinfo": "footer",
            "main":       "main",
            "article":    "article",
            "region":     "section",
            "button":     "button",
            "link":       "a",
            "form":       "form",
            "heading":    "h2",
            "img":        "img",
        }.get(spec.a11y.role.value, "div")

    # ============================================================
    # 4. APP.VUE
    # ============================================================

    def _build_app_sfc(
        self,
        graph: DesignGraph,
        used_ids: Set[str],
    ) -> FileModule:
        # Script: imports + data hooks
        script_lines = [
            "<script setup lang=\"ts\">",
            "// Auto-generated by APEX FACTORY v6.0 - VueEmitter",
            f"// DesignGraph: {graph.graph_id}",
        ]
        # Imports
        for cid in sorted(used_ids):
            if cid in HTML_TAGS:
                continue
            comp_name = to_pascal_case(cid)
            script_lines.append(
                f'import {comp_name} from "./{self.config.components_subdir}/'
                f'{comp_name}/{comp_name}.vue";'
            )
        # Import styles
        script_lines.append(
            f'import "./{self.config.styles_subdir}/tokens.css";'
        )
        # Data hooks (ref/reactive)
        needs_ref = any(
            ds.kind == DataSourceKind.STATE for ds in graph.data_sources.values()
        )
        if needs_ref:
            script_lines.append('import { ref } from "vue";')
        script_lines.append("")
        for ds_id, ds in graph.data_sources.items():
            var_name = to_camel_case(ds_id)
            if ds.kind == DataSourceKind.STATIC:
                raw = json.dumps(ds.config.get("value"), ensure_ascii=False)
                script_lines.append(
                    f"const {var_name}: {ds.shape_hint} = {raw};"
                )
            elif ds.kind == DataSourceKind.STATE:
                initial = ds.config.get("initial", None)
                initial_str = json.dumps(initial, ensure_ascii=False)
                script_lines.append(
                    f"const {var_name} = ref<{ds.shape_hint}>({initial_str});"
                )
            elif ds.kind == DataSourceKind.REST:
                url = ds.config.get("url", "/api/unknown")
                script_lines.append(f"// TODO REST data source: {var_name} (GET {url})")
                script_lines.append(
                    f"const {var_name} = ref<{ds.shape_hint} | null>(null);"
                )

        script_lines.append("</script>")

        # Template: recursive render của root node
        template_body = self._node_to_template(graph.get_root(), graph, depth=1)
        template_lines = ["<template>", template_body, "</template>"]

        content = "\n".join(script_lines + [""] + template_lines) + "\n"

        mod = FileModule(
            file_path=f"{self.config.target_src_dir}/App.vue",
            language="vue",
        )
        mod.top_level.append(content)
        mod.trailing_newline = False
        return mod

    def _node_to_template(
        self, node: DesignNode, graph: DesignGraph, depth: int = 0
    ) -> str:
        if depth > 20:
            return "  " * depth + f"<!-- max depth at {node.node_id} -->"

        indent = "  " * depth
        is_html = node.component_id in HTML_TAGS
        tag = node.component_id if is_html else to_pascal_case(node.component_id)

        # Attributes
        attrs: List[str] = []
        for prop_name, prop_value in node.props.items():
            if prop_name == "children":
                continue
            if isinstance(prop_value, str):
                attrs.append(f'{prop_name}="{prop_value}"')
            else:
                attrs.append(f':{prop_name}="{json.dumps(prop_value)}"')

        for prop_name, source_id in node.data_bindings.items():
            var_name = to_camel_case(source_id)
            attrs.append(f':{prop_name}="{var_name}"')

        for event_name, handler in node.event_handlers.items():
            # Vue syntax: @click, @input...
            vue_event = event_name
            if vue_event.startswith("on"):
                vue_event = "@" + vue_event[2:].lower()
            attrs.append(f'{vue_event}="{handler}"')

        # Class
        cl = ClassList()
        base_class = node.props.get("className")
        if isinstance(base_class, str):
            cl.add(base_class)
        for bp, ov in node.responsive_overrides.items():
            if isinstance(ov, dict):
                bp_cls = ov.get("className")
                if isinstance(bp_cls, str):
                    for t in bp_cls.split():
                        cl.add(f"{bp}:{t}")
        if cl.to_list():
            attrs.append(f'class="{cl.render()}"')

        attr_str = " ".join(attrs)

        # Children
        children_str_parts: List[str] = []
        slot_order = ["default"] + [s for s in node.children_by_slot if s != "default"]
        for slot_name in slot_order:
            for child_id in node.children_by_slot.get(slot_name, []):
                child = graph.nodes.get(child_id)
                if child is None:
                    continue
                children_str_parts.append(
                    self._node_to_template(child, graph, depth + 1)
                )

        if not children_str_parts:
            open_tag_prefix = f"<{tag}"
            return f"{indent}{open_tag_prefix}{' ' + attr_str if attr_str else ''} />"

        open_tag = f"<{tag}{' ' + attr_str if attr_str else ''}>"
        close_tag = f"</{tag}>"
        inner = "\n".join(children_str_parts)
        return f"{indent}{open_tag}\n{inner}\n{indent}{close_tag}"

    # ============================================================
    # 5. main.ts + scaffold
    # ============================================================

    def _build_main_ts(self) -> FileModule:
        content = (
            "// APEX FACTORY v6.0 - Vue entry point\n"
            "import { createApp } from 'vue';\n"
            "import App from './App.vue';\n"
            "createApp(App).mount('#app');\n"
        )
        mod = FileModule(
            file_path=f"{self.config.target_src_dir}/main.ts",
            language="typescript",
        )
        mod.top_level.append(content)
        mod.trailing_newline = False
        return mod

    def _render_vite_config(self) -> str:
        return (
            "import { defineConfig } from 'vite';\n"
            "import vue from '@vitejs/plugin-vue';\n"
            "// APEX FACTORY v6.0 - Vue target\n"
            "export default defineConfig({\n"
            "  plugins: [vue()],\n"
            "  server: { port: 5173, host: '0.0.0.0' },\n"
            "  build: { sourcemap: true, target: 'es2020' },\n"
            "});\n"
        )

    def _render_tsconfig(self) -> str:
        return json.dumps({
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "moduleResolution": "bundler",
                "strict": True,
                "jsx": "preserve",
                "skipLibCheck": True,
                "esModuleInterop": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "types": ["vite/client"],
            },
            "include": [self.config.target_src_dir, "vite.config.ts"],
        }, indent=2) + "\n"

    def _render_package_json(self) -> str:
        return json.dumps({
            "name": self.config.app_name + "-vue",
            "version": "0.1.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vue-tsc --noEmit && vite build",
                "preview": "vite preview",
            },
            "dependencies": {"vue": VUE_VERSION},
            "devDependencies": {
                "@vitejs/plugin-vue": VITE_PLUGIN_VUE_VERSION,
                "autoprefixer": "^10.4.19",
                "postcss": "^8.4.38",
                "tailwindcss": "^3.4.3",
                "typescript": "^5.4.5",
                "vite": "^5.2.0",
                "vue-tsc": "^2.0.0",
            },
            "engines": {"node": ">=18.0.0"},
        }, indent=2) + "\n"

    def _render_index_html(self) -> str:
        return (
            "<!DOCTYPE html>\n"
            '<html lang="vi">\n<head>\n'
            '  <meta charset="UTF-8" />\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            f"  <title>{self.config.app_title}</title>\n"
            "</head>\n<body>\n"
            '  <div id="app"></div>\n'
            f'  <script type="module" src="/{self.config.target_src_dir}/main.ts"></script>\n'
            "</body>\n</html>\n"
        )


# ============================================================
# 6. SANITY CHECK
# ============================================================

def vue_emitter_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ontology_ui import (
        A11yContract,
        A11yRole,
        ColorToken,
        ComponentCategory,
        ComponentSpec,
        ComponentState,
        PropSchema,
        SlotSchema,
        TokenRole,
    )
    from apex_core.foundation.ui_ir import DesignGraph, DesignNode

    checks: Dict[str, bool] = {}

    cat = ComponentCatalog()
    cat.register(ComponentSpec(
        component_id="organism.navbar",
        label="Navbar",
        category=ComponentCategory.ORGANISM,
        prop_schema=(PropSchema("brand", "string", required=True),),
        slots=(SlotSchema(name="default"),),
        states=(ComponentState.DEFAULT,),
        a11y=A11yContract(role=A11yRole.NAVIGATION),
        design_tokens_used=(),
        dependencies=(),
        render_targets=(RenderTarget.VUE,),
    ))

    reg = TokenRegistry()
    reg.add(ColorToken(token_id="brand.primary", value="#2563EB", role=TokenRole.PRIMARY))
    reg.freeze()

    g = DesignGraph(graph_id="g_vue", target=RenderTarget.VUE, root_id="root")
    g.add_node(DesignNode(node_id="root", component_id="div"))
    g.add_node(DesignNode(
        node_id="nav", component_id="organism.navbar",
        props={"brand": "Acme"},
    ))
    g.link("root", "default", "nav")

    result = VueEmitter(cat, reg).emit_graph(g)
    checks["emit_ok"] = isinstance(result, EmitResult)
    checks["has_app_vue"] = any(f.file_path.endswith("App.vue") for f in result.files)
    checks["has_main_ts"] = any(f.file_path.endswith("main.ts") for f in result.files)
    checks["has_navbar_vue"] = any(
        f.file_path.endswith("OrganismNavbar/OrganismNavbar.vue") for f in result.files
    )
    # Render App.vue
    app = next(f for f in result.files if f.file_path.endswith("App.vue"))
    app_content = app.render()
    checks["app_imports_navbar"] = 'from "./components/OrganismNavbar/OrganismNavbar.vue"' in app_content
    checks["app_has_template"] = "<template>" in app_content and "</template>" in app_content
    checks["app_uses_script_setup"] = '<script setup lang="ts">' in app_content
    # Package json
    pkg = json.loads(result.scaffold_files["package.json"])
    checks["pkg_has_vue"] = "vue" in pkg["dependencies"]
    return checks


__all__ = [
    "VUE_EMITTER_VERSION", "VUE_VERSION",
    "VueEmitter",
    "vue_emitter_sanity_check",
]
