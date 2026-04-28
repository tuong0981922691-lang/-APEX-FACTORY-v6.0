"""Runnable APEX Factory facade."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from apex_core.foundation.ontology_ui import (
    ComponentCatalog,
    TokenRegistry,
    build_default_catalog,
    build_default_registry,
    ontology_ui_sanity_check,
)
from apex_core.legacy.foundation.capability_token import (
    CapabilityGate,
    CapabilityTokenSigner,
    KillSwitch,
    NonceStore,
)
from apex_core.legacy.foundation.contracts import now_utc_iso

APEX_FACTORY_VERSION = "6.0.0-scaffold"
BANNER = "APEX FACTORY v6.0 - Runnable Scaffold"


@dataclass
class ApexFactoryConfig:
    storage_dir: Path = Path("./apex_factory_storage")
    enable_llm: bool = False


@dataclass
class ApexFactory:
    """Small but functional facade that keeps the blueprint entrypoint alive."""

    config: ApexFactoryConfig = field(default_factory=ApexFactoryConfig)
    catalog: ComponentCatalog = field(default_factory=build_default_catalog)
    registry: TokenRegistry = field(default_factory=build_default_registry)

    def __post_init__(self) -> None:
        self.config.storage_dir.mkdir(parents=True, exist_ok=True)
        self.kill_switch = KillSwitch(self.config.storage_dir / "KILL_SWITCH")
        self.nonce_store = NonceStore()
        self.signer = CapabilityTokenSigner()
        self.capability_gate = CapabilityGate(self.signer, self.nonce_store)
        self.booted_at = now_utc_iso()

    def boot(self) -> Dict[str, Any]:
        return {
            "ok": not self.kill_switch.is_activated(),
            "version": APEX_FACTORY_VERSION,
            "booted_at": self.booted_at,
            "checks": ontology_ui_sanity_check(),
        }

    def get_health_snapshot(self) -> Dict[str, Any]:
        checks = ontology_ui_sanity_check()
        return {
            "status": "killed" if self.kill_switch.is_activated() else "ready",
            "version": APEX_FACTORY_VERSION,
            "booted_at": self.booted_at,
            "storage_dir": str(self.config.storage_dir),
            "capability_tokens_configured": self.signer.configured,
            "kill_switch_active": self.kill_switch.is_activated(),
            "components": len(self.catalog.list_components()),
            "tokens": len(self.registry.list_tokens()),
            "checks": checks,
        }

    def build_web_project(self, brief: str) -> Dict[str, Any]:
        return {
            "ok": True,
            "brief": brief,
            "message": "Blueprint scaffold accepted the build brief; emitters will be materialized in a later phase.",
            "available_components": [component.component_id for component in self.catalog.list_components()],
        }


def apex_factory_sanity_check() -> Dict[str, bool]:
    factory = ApexFactory()
    health = factory.get_health_snapshot()
    return {
        "factory_ready": health["status"] == "ready",
        "has_components": health["components"] >= 1,
        "has_tokens": health["tokens"] >= 1,
    }


__all__ = [
    "APEX_FACTORY_VERSION",
    "BANNER",
    "ApexFactory",
    "ApexFactoryConfig",
    "apex_factory_sanity_check",
]
