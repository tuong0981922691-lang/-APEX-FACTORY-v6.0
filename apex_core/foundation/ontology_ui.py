"""Minimal UI ontology used by the runnable APEX Factory scaffold."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class DesignToken:
    """A named design token stored by the registry."""

    token_id: str
    value: str
    role: str = "general"


@dataclass
class TokenRegistry:
    """In-memory design token registry with freeze enforcement."""

    _tokens: Dict[str, DesignToken] = field(default_factory=dict)
    _frozen: bool = False

    def register(self, token: DesignToken) -> None:
        if self._frozen:
            raise RuntimeError("TokenRegistry is frozen")
        self._tokens[token.token_id] = token

    def get(self, token_id: str) -> DesignToken:
        return self._tokens[token_id]

    def list_tokens(self) -> List[DesignToken]:
        return list(self._tokens.values())

    def freeze(self) -> None:
        self._frozen = True

    @property
    def frozen(self) -> bool:
        return self._frozen


@dataclass(frozen=True)
class ComponentSpec:
    """A compact component contract."""

    component_id: str
    category: str
    render_targets: frozenset[str] = frozenset({"react"})

    def supports_target(self, target: str) -> bool:
        return target in self.render_targets


@dataclass
class ComponentCatalog:
    """Registry for component specifications."""

    _components: Dict[str, ComponentSpec] = field(default_factory=dict)

    def register(self, spec: ComponentSpec) -> None:
        self._components[spec.component_id] = spec

    def get(self, component_id: str) -> ComponentSpec:
        return self._components[component_id]

    def list_components(self) -> List[ComponentSpec]:
        return list(self._components.values())

    def search_by_target(self, target: str) -> List[ComponentSpec]:
        return [spec for spec in self._components.values() if spec.supports_target(target)]


def build_default_registry() -> TokenRegistry:
    registry = TokenRegistry()
    registry.register(DesignToken("color.primary", "#2563eb", "primary"))
    registry.register(DesignToken("space.4", "1rem", "spacing"))
    registry.freeze()
    return registry


def build_default_catalog() -> ComponentCatalog:
    catalog = ComponentCatalog()
    for component_id, category in (
        ("atom.button.primary", "atom"),
        ("organism.hero.simple", "organism"),
        ("page.landing", "page"),
    ):
        catalog.register(ComponentSpec(component_id=component_id, category=category))
    return catalog


def ontology_ui_sanity_check() -> Dict[str, bool]:
    registry = build_default_registry()
    catalog = build_default_catalog()
    frozen_enforced = False
    try:
        registry.register(DesignToken("color.secondary", "#111827"))
    except RuntimeError:
        frozen_enforced = True
    return {
        "registry_has_tokens": len(registry.list_tokens()) >= 2,
        "catalog_has_components": len(catalog.list_components()) >= 3,
        "token_registry_freeze_enforced": frozen_enforced,
    }


__all__ = [
    "ComponentCatalog",
    "ComponentSpec",
    "DesignToken",
    "TokenRegistry",
    "build_default_catalog",
    "build_default_registry",
    "ontology_ui_sanity_check",
]
