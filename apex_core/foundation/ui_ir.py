"""
APEX FACTORY v6.0 - Foundation Extension
File: ui_ir.py

Mục đích: UI-IR (Intermediate Representation) - ngôn ngữ trung gian
          biểu diễn 1 trang/app dưới dạng DAG, độc lập framework.

Luồng: Brief → B4 Composition → DesignGraph (UI-IR) → Emitter → React/Vue/...

Triết lý: UI-IR giống 'AST' của chương trình nhưng ở tầng UI tree.
          Mọi thao tác (phân tích, tối ưu, diff, patch) xảy ra trên UI-IR,
          không trên source code framework-specific.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Mapping, Optional, Set, Tuple

from apex_core.foundation.ontology_ui import (
    Breakpoint,
    ComponentCatalog,
    RenderTarget,
)

# ============================================================
# 0. VERSION
# ============================================================

UI_IR_VERSION = "6.0.0"
UI_IR_SCHEMA = "apex.factory.ui-ir/v6"


# ============================================================
# 1. BINDING TYPES (cạnh của DAG)
# ============================================================

class BindingKind(str, Enum):
    SLOT = "slot"               # parent -> child qua slot name
    PROP = "prop"               # bind giá trị vào prop
    EVENT = "event"             # bind event handler
    DATA = "data"               # bind data source
    STYLE_OVERRIDE = "style"    # override token-level


@dataclass(frozen=True)
class Binding:
    kind: BindingKind
    name: str                   # slot name / prop name / event name
    source: Optional[str] = None  # id của node/data source
    value: Any = None
    note: str = ""


# ============================================================
# 2. DESIGN NODE (đỉnh của DAG)
# ============================================================

@dataclass
class DesignNode:
    """
    1 đỉnh trong DesignGraph. Tương đương 1 JSX element instance.
    Mutable trong giai đoạn xây dựng, sẽ freeze khi xuất IR.
    """
    node_id: str                              # UUID-like
    component_id: str                         # FK vào ComponentCatalog
    props: Dict[str, Any] = field(default_factory=dict)
    data_bindings: Dict[str, str] = field(default_factory=dict)
    event_handlers: Dict[str, str] = field(default_factory=dict)
    responsive_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # breakpoint_value -> {prop_name: override_value}
    children_by_slot: Dict[str, List[str]] = field(default_factory=dict)
    # slot_name -> [child_node_ids]
    style_overrides: Dict[str, str] = field(default_factory=dict)
    # css_var_name -> token_id_override
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_child(self, slot_name: str, child_id: str) -> None:
        self.children_by_slot.setdefault(slot_name, []).append(child_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "component_id": self.component_id,
            "props": dict(self.props),
            "data_bindings": dict(self.data_bindings),
            "event_handlers": dict(self.event_handlers),
            "responsive_overrides": {
                bp: dict(overrides) for bp, overrides in self.responsive_overrides.items()
            },
            "children_by_slot": {
                slot: list(ids) for slot, ids in self.children_by_slot.items()
            },
            "style_overrides": dict(self.style_overrides),
            "notes": self.notes,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "DesignNode":
        return cls(
            node_id=d["node_id"],
            component_id=d["component_id"],
            props=dict(d.get("props", {})),
            data_bindings=dict(d.get("data_bindings", {})),
            event_handlers=dict(d.get("event_handlers", {})),
            responsive_overrides={
                bp: dict(v) for bp, v in (d.get("responsive_overrides") or {}).items()
            },
            children_by_slot={
                slot: list(v) for slot, v in (d.get("children_by_slot") or {}).items()
            },
            style_overrides=dict(d.get("style_overrides", {})),
            notes=d.get("notes", ""),
            metadata=dict(d.get("metadata", {})),
        )


# ============================================================
# 3. DATA SOURCE (cho binding động)
# ============================================================

class DataSourceKind(str, Enum):
    STATIC = "static"           # giá trị tĩnh
    REST = "rest"               # GET/POST endpoint
    GRAPHQL = "graphql"
    STATE = "state"             # local state
    CONTEXT = "context"         # React Context / Vue Provide
    ROUTE_PARAM = "route_param"


@dataclass(frozen=True)
class DataSource:
    source_id: str
    kind: DataSourceKind
    config: Mapping[str, Any] = field(default_factory=dict)
    shape_hint: str = "any"     # "User", "Product[]", ... (TS-like)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "kind": self.kind.value,
            "config": dict(self.config),
            "shape_hint": self.shape_hint,
        }


# ============================================================
# 4. DESIGN GRAPH (DAG)
# ============================================================

@dataclass
class DesignGraph:
    """
    Toàn bộ 1 page/component tree dưới dạng DAG.
    Có đúng 1 root node.
    """
    graph_id: str
    target: RenderTarget
    root_id: str
    nodes: Dict[str, DesignNode] = field(default_factory=dict)
    data_sources: Dict[str, DataSource] = field(default_factory=dict)
    theme_profile: str = "default"      # "default" | "dark" | "high-contrast" ...
    breakpoint_set: Tuple[Breakpoint, ...] = (
        Breakpoint.SM, Breakpoint.MD, Breakpoint.LG, Breakpoint.XL,
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    # --------- Mutation API ---------
    def add_node(self, node: DesignNode) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node_id: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_data_source(self, ds: DataSource) -> None:
        if ds.source_id in self.data_sources:
            raise ValueError(f"Duplicate data_source: {ds.source_id}")
        self.data_sources[ds.source_id] = ds

    def link(self, parent_id: str, slot: str, child_id: str) -> None:
        if parent_id not in self.nodes:
            raise KeyError(f"Parent node not found: {parent_id}")
        if child_id not in self.nodes:
            raise KeyError(f"Child node not found: {child_id}")
        if parent_id == child_id:
            raise ValueError("Cannot link node to itself")
        self.nodes[parent_id].add_child(slot, child_id)

    # --------- Query API ---------
    def get_root(self) -> DesignNode:
        node = self.nodes.get(self.root_id)
        if node is None:
            raise KeyError(f"Root node not found: {self.root_id}")
        return node

    def walk(self, start_id: Optional[str] = None) -> Iterator[Tuple[int, DesignNode]]:
        """DFS yield (depth, node)."""
        start = start_id or self.root_id
        if start not in self.nodes:
            return
        stack: List[Tuple[int, str]] = [(0, start)]
        visited: Set[str] = set()
        while stack:
            depth, nid = stack.pop()
            if nid in visited:
                continue
            visited.add(nid)
            node = self.nodes.get(nid)
            if node is None:
                continue
            yield depth, node
            for slot_name in reversed(list(node.children_by_slot.keys())):
                for child_id in reversed(node.children_by_slot[slot_name]):
                    stack.append((depth + 1, child_id))

    def descendants(self, node_id: str) -> Set[str]:
        ids: Set[str] = set()
        for _, node in self.walk(node_id):
            if node.node_id != node_id:
                ids.add(node.node_id)
        return ids

    def find_by_component(self, component_id: str) -> List[DesignNode]:
        return [n for n in self.nodes.values() if n.component_id == component_id]

    # --------- Validation ---------
    def validate(self, catalog: ComponentCatalog) -> List[str]:
        """Trả về danh sách vi phạm. Rỗng = OK."""
        violations: List[str] = []

        # 1. Root tồn tại
        if self.root_id not in self.nodes:
            violations.append(f"Root node missing: {self.root_id}")
            return violations   # các check khác vô nghĩa nếu thiếu root

        # 2. Mọi node.component_id có trong catalog + support target
        for nid, node in self.nodes.items():
            spec = catalog.get(node.component_id)
            if spec is None:
                violations.append(f"Node {nid}: component not in catalog ({node.component_id})")
                continue
            if not spec.supports_target(self.target):
                violations.append(
                    f"Node {nid}: component {spec.component_id} không hỗ trợ {self.target.value}"
                )
            # Required prop check
            for prop in spec.prop_schema:
                if prop.required and prop.name not in node.props \
                        and prop.name not in node.data_bindings:
                    violations.append(
                        f"Node {nid}: missing required prop '{prop.name}'"
                    )
            # Slot membership check
            for slot_name, child_ids in node.children_by_slot.items():
                slot = spec.get_slot(slot_name)
                if slot is None:
                    violations.append(
                        f"Node {nid}: slot '{slot_name}' không có trong {spec.component_id}"
                    )
                    continue
                if slot.max_children is not None and len(child_ids) > slot.max_children:
                    violations.append(
                        f"Node {nid} slot '{slot_name}': vượt max_children "
                        f"({len(child_ids)} > {slot.max_children})"
                    )
                # Category membership
                if slot.accepts_categories:
                    for cid in child_ids:
                        child = self.nodes.get(cid)
                        if child is None:
                            continue
                        child_spec = catalog.get(child.component_id)
                        if child_spec is None:
                            continue
                        if child_spec.category.value not in slot.accepts_categories:
                            violations.append(
                                f"Node {nid} slot '{slot_name}': child {cid} category "
                                f"'{child_spec.category.value}' không được chấp nhận"
                            )

        # 3. DAG (no cycle)
        cycle = self._detect_cycle()
        if cycle:
            violations.append(f"Cycle detected: {' -> '.join(cycle)}")

        # 4. Không có node mồ côi (orphan - ngoài root)
        reachable = {n.node_id for _, n in self.walk()}
        orphans = set(self.nodes.keys()) - reachable
        if orphans:
            violations.append(f"Orphan nodes: {sorted(orphans)}")

        # 5. Data binding phải trỏ tới data_source hoặc node khác
        for nid, node in self.nodes.items():
            for prop_name, source_ref in node.data_bindings.items():
                if source_ref not in self.data_sources and source_ref not in self.nodes:
                    violations.append(
                        f"Node {nid} data binding '{prop_name}' trỏ tới ref không tồn tại: {source_ref}"
                    )

        return violations

    def _detect_cycle(self) -> List[str]:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {nid: WHITE for nid in self.nodes}
        parent: Dict[str, Optional[str]] = {nid: None for nid in self.nodes}

        def dfs(u: str) -> Optional[List[str]]:
            color[u] = GRAY
            for slot_children in self.nodes[u].children_by_slot.values():
                for v in slot_children:
                    if v not in color:
                        continue
                    if color[v] == GRAY:
                        # reconstruct cycle
                        path = [v, u]
                        p = parent[u]
                        while p is not None and p != v:
                            path.append(p)
                            p = parent[p]
                        if p == v:
                            path.append(v)
                        return list(reversed(path))
                    if color[v] == WHITE:
                        parent[v] = u
                        found = dfs(v)
                        if found:
                            return found
            color[u] = BLACK
            return None

        for nid in self.nodes:
            if color[nid] == WHITE:
                found = dfs(nid)
                if found:
                    return found
        return []

    # --------- Serialization ---------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": UI_IR_SCHEMA,
            "version": UI_IR_VERSION,
            "graph_id": self.graph_id,
            "target": self.target.value,
            "root_id": self.root_id,
            "theme_profile": self.theme_profile,
            "breakpoint_set": [b.value for b in self.breakpoint_set],
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "data_sources": {sid: ds.to_dict() for sid, ds in self.data_sources.items()},
            "metadata": dict(self.metadata),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, default=str)

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "DesignGraph":
        if d.get("schema") != UI_IR_SCHEMA:
            raise ValueError(f"Unsupported UI-IR schema: {d.get('schema')}")
        g = cls(
            graph_id=d["graph_id"],
            target=RenderTarget(d["target"]),
            root_id=d["root_id"],
            theme_profile=d.get("theme_profile", "default"),
            breakpoint_set=tuple(
                Breakpoint(bp) for bp in d.get("breakpoint_set", [])
            ) or (Breakpoint.SM, Breakpoint.MD, Breakpoint.LG, Breakpoint.XL),
            metadata=dict(d.get("metadata", {})),
        )
        for nid, nd in d.get("nodes", {}).items():
            g.nodes[nid] = DesignNode.from_dict(nd)
        for sid, sd in d.get("data_sources", {}).items():
            g.data_sources[sid] = DataSource(
                source_id=sd["source_id"],
                kind=DataSourceKind(sd["kind"]),
                config=dict(sd.get("config", {})),
                shape_hint=sd.get("shape_hint", "any"),
            )
        return g

    def content_hash(self) -> str:
        """SHA-256 hash stable, dùng cho audit + diff."""
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()


# ============================================================
# 5. BUILDER (DSL thân thiện để dựng DAG)
# ============================================================

class DesignGraphBuilder:
    """
    Builder pattern cho DesignGraph để tránh code dài lê thê khi build thủ công.

    Usage:
        g = (DesignGraphBuilder(RenderTarget.REACT)
             .root("organism.navbar.default", props={"brand": "Acme"})
             .child("atom.button.primary", slot="actions", props={"label": "Sign up"})
             .up()
             .build())
    """

    def __init__(self, target: RenderTarget, graph_id: Optional[str] = None):
        self._target = target
        self._graph = DesignGraph(
            graph_id=graph_id or self._gen_id("g"),
            target=target,
            root_id="",   # sẽ set khi gọi .root()
        )
        self._stack: List[Tuple[str, str]] = []   # (parent_node_id, slot_name)

    @staticmethod
    def _gen_id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def root(
        self,
        component_id: str,
        *,
        node_id: Optional[str] = None,
        props: Optional[Mapping[str, Any]] = None,
    ) -> "DesignGraphBuilder":
        if self._graph.root_id:
            raise RuntimeError("Root already set")
        nid = node_id or self._gen_id("n")
        node = DesignNode(
            node_id=nid,
            component_id=component_id,
            props=dict(props or {}),
        )
        self._graph.add_node(node)
        self._graph.root_id = nid
        self._stack.append((nid, "default"))
        return self

    def child(
        self,
        component_id: str,
        *,
        slot: str = "default",
        node_id: Optional[str] = None,
        props: Optional[Mapping[str, Any]] = None,
        enter: bool = True,
    ) -> "DesignGraphBuilder":
        if not self._stack:
            raise RuntimeError("Call .root() first")
        parent_id, _ = self._stack[-1]
        nid = node_id or self._gen_id("n")
        node = DesignNode(
            node_id=nid,
            component_id=component_id,
            props=dict(props or {}),
        )
        self._graph.add_node(node)
        self._graph.link(parent_id, slot, nid)
        if enter:
            self._stack.append((nid, slot))
        return self

    def up(self) -> "DesignGraphBuilder":
        if len(self._stack) <= 1:
            raise RuntimeError("Already at root")
        self._stack.pop()
        return self

    def bind_data(
        self,
        source_id: str,
        kind: DataSourceKind,
        *,
        config: Optional[Mapping[str, Any]] = None,
        shape_hint: str = "any",
    ) -> "DesignGraphBuilder":
        self._graph.add_data_source(DataSource(
            source_id=source_id,
            kind=kind,
            config=dict(config or {}),
            shape_hint=shape_hint,
        ))
        return self

    def set_prop(self, prop_name: str, value: Any) -> "DesignGraphBuilder":
        parent_id, _ = self._stack[-1]
        self._graph.nodes[parent_id].props[prop_name] = value
        return self

    def bind_prop(self, prop_name: str, source_id: str) -> "DesignGraphBuilder":
        parent_id, _ = self._stack[-1]
        self._graph.nodes[parent_id].data_bindings[prop_name] = source_id
        return self

    def build(self, catalog: Optional[ComponentCatalog] = None) -> DesignGraph:
        if catalog is not None:
            violations = self._graph.validate(catalog)
            if violations:
                raise ValueError(f"DesignGraph invalid: {violations}")
        return self._graph


# ============================================================
# 6. DIFF UTILITIES (dùng sau cho Forge hot-patch)
# ============================================================

@dataclass(frozen=True)
class GraphDiff:
    added_nodes: Tuple[str, ...]
    removed_nodes: Tuple[str, ...]
    modified_nodes: Tuple[str, ...]

    def is_empty(self) -> bool:
        return not (self.added_nodes or self.removed_nodes or self.modified_nodes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "added": list(self.added_nodes),
            "removed": list(self.removed_nodes),
            "modified": list(self.modified_nodes),
        }


def diff_graphs(before: DesignGraph, after: DesignGraph) -> GraphDiff:
    """Diff đơn giản theo node_id + content hash."""
    before_ids = set(before.nodes.keys())
    after_ids = set(after.nodes.keys())

    added = tuple(sorted(after_ids - before_ids))
    removed = tuple(sorted(before_ids - after_ids))

    common = before_ids & after_ids
    modified: List[str] = []
    for nid in sorted(common):
        b_hash = hashlib.sha256(
            json.dumps(before.nodes[nid].to_dict(), sort_keys=True, default=str).encode()
        ).hexdigest()
        a_hash = hashlib.sha256(
            json.dumps(after.nodes[nid].to_dict(), sort_keys=True, default=str).encode()
        ).hexdigest()
        if b_hash != a_hash:
            modified.append(nid)

    return GraphDiff(
        added_nodes=added,
        removed_nodes=removed,
        modified_nodes=tuple(modified),
    )


# ============================================================
# 7. SANITY CHECK
# ============================================================

def ui_ir_sanity_check() -> Dict[str, bool]:
    """Self-test - gọi khi boot."""
    checks: Dict[str, bool] = {}

    try:
        g = DesignGraph(
            graph_id="g_test",
            target=RenderTarget.REACT,
            root_id="n_root",
        )
        g.add_node(DesignNode(node_id="n_root", component_id="atom.box"))
        g.add_node(DesignNode(node_id="n_child", component_id="atom.button"))
        g.link("n_root", "default", "n_child")
        checks["basic_link"] = "n_child" in g.nodes["n_root"].children_by_slot["default"]
    except Exception:
        checks["basic_link"] = False

    # Cycle detection
    try:
        g2 = DesignGraph(
            graph_id="g_cycle",
            target=RenderTarget.REACT,
            root_id="a",
        )
        g2.add_node(DesignNode(node_id="a", component_id="atom.box"))
        g2.add_node(DesignNode(node_id="b", component_id="atom.box"))
        g2.link("a", "default", "b")
        # inject cycle manually
        g2.nodes["b"].add_child("default", "a")
        cycle = g2._detect_cycle()
        checks["cycle_detected"] = len(cycle) > 0
    except Exception:
        checks["cycle_detected"] = False

    # Serialize round-trip
    try:
        g = DesignGraph(graph_id="g_rt", target=RenderTarget.REACT, root_id="r")
        g.add_node(DesignNode(node_id="r", component_id="atom.box"))
        d = g.to_dict()
        g2 = DesignGraph.from_dict(d)
        checks["serialize_roundtrip"] = g2.content_hash() == g.content_hash()
    except Exception:
        checks["serialize_roundtrip"] = False

    # Diff
    try:
        g1 = DesignGraph(graph_id="g1", target=RenderTarget.REACT, root_id="r")
        g1.add_node(DesignNode(node_id="r", component_id="atom.box"))
        g2 = DesignGraph(graph_id="g2", target=RenderTarget.REACT, root_id="r")
        g2.add_node(DesignNode(node_id="r", component_id="atom.box"))
        g2.add_node(DesignNode(node_id="x", component_id="atom.button"))
        g2.link("r", "default", "x")
        diff = diff_graphs(g1, g2)
        checks["diff_detects_add"] = "x" in diff.added_nodes
    except Exception:
        checks["diff_detects_add"] = False

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "UI_IR_VERSION",
    "UI_IR_SCHEMA",
    "BindingKind",
    "Binding",
    "DesignNode",
    "DataSourceKind",
    "DataSource",
    "DesignGraph",
    "DesignGraphBuilder",
    "GraphDiff",
    "diff_graphs",
    "ui_ir_sanity_check",
]
