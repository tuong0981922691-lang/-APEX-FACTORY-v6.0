"""
APEX FACTORY v6.0 - Orchestrator Layer (v6)
File: apex_factory.py

Mục đích: Facade TỐI THƯỢNG. Thay thế ApexTitan v5.0.
    1 class duy nhất orchestrate toàn bộ 6 phase:
      - Phase 0: Foundation (ontology UI/media, project snapshot)
      - Phase 1: 7 Brains v6 (IntentIngestor → RuntimeForge)
      - Phase 2: Deliberation (Radar 4D + Round Table V6 + Quality Gate)
      - Phase 3: Emitters (React + Vue) + Preview Sandbox
      - Phase 4: Evolution (ErrorLedger + ASTSurgeon + HotInject)
      - Phase 5: External (LLM Broker + Schema Guard)
      - Phase 6: Factories (Web/Mobile/Video/Image + Deploy)

Triết lý NT5: C2 tương tác DUY NHẤT với ApexFactory. Mọi chi tiết kỹ thuật
              ẩn phía sau facade. Mọi mệnh lệnh quan trọng cần Capability Token.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Phase 3 - Emitters
from apex_core.emitters.react_emitter import EmitConfig, ReactEmitter

# Phase 4 - Evolution
from apex_core.evolution_v6.ast_surgeon_v6 import ASTSurgeonV6
from apex_core.evolution_v6.error_ledger_v6 import (
    ErrorLedgerV6,
    RotationPolicy,
)
from apex_core.evolution_v6.hot_inject import (
    HotInjectEngine,
    InjectRequest,
    InjectResult,
)

# Phase 5 - External
from apex_core.external.llm_broker import (
    AnthropicAdapter,
    BrokerConfig,
    GeminiAdapter,
    LLMAdapter,
    LLMBroker,
    MockAdapter,
    OllamaAdapter,
    OpenAIAdapter,
)
from apex_core.external.schema_guard import SchemaGuard

# Phase 6 - Factories
from apex_core.factories.deploy_adapter import (
    DeployAdapter,
    DeployLedger,
    DeployRequest,
    DeployResult,
)
from apex_core.factories.image_factory import (
    ImageFactory,
    ImageFactoryConfig,
    ImageGenRequest,
    ImageGenResult,
    ImageProviderAdapter,
    MockImageProvider,
)
from apex_core.factories.mobile_factory import (
    MobileFactory,
    MobileFactoryConfig,
)
from apex_core.factories.video_factory import (
    VideoFactory,
    VideoFactoryConfig,
)
from apex_core.factories.web_factory import (
    BuildArtifact,
    WebFactory,
    WebFactoryConfig,
)
from apex_core.foundation.composition_rules import composition_rules_sanity_check

# Foundation
from apex_core.foundation.domain_types import DomainRegistry, DomainType
from apex_core.foundation.ontology_media import SceneGraph, ontology_media_sanity_check
from apex_core.foundation.ontology_ui import (
    ComponentCatalog,
    TokenRegistry,
    ontology_ui_sanity_check,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
    principles_v6_sanity_check,
)
from apex_core.foundation.project_snapshot import ProjectLineage
from apex_core.foundation.ui_ir import DesignGraph

# Legacy security core (kế thừa nguyên vẹn)
from apex_core.legacy.foundation.capability_token import (
    ALLOWED_SCOPES,
    CapabilityGate,
    CapabilityToken,
    CapabilityTokenSigner,
    KillSwitch,
    NonceStore,
)

# ============================================================
# 0. VERSION + METADATA
# ============================================================

APEX_FACTORY_VERSION = "6.0.0"
APEX_FACTORY_CODENAME = "APEX_FACTORY_OMNIDOMAIN"

BANNER = f"""
🏭 APEX FACTORY v{APEX_FACTORY_VERSION} - {APEX_FACTORY_CODENAME}
    Omni-Domain Production System
    Successor of APEX TITAN v5.0
""".strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 1. CONFIG
# ============================================================

@dataclass
class ApexFactoryConfig:
    # Storage
    storage_root: Path = field(default_factory=lambda: Path("./apex_factory_storage"))

    # Domain defaults
    default_domain: DomainType = DomainType.WEB

    # Web factory sub-config
    web_config: Optional[WebFactoryConfig] = None

    # LLM Broker
    llm_cost_cap_usd: float = 5.0
    llm_audit_enabled: bool = True
    llm_adapters: Optional[List[LLMAdapter]] = None

    # Image factory
    image_adapters: Optional[List[ImageProviderAdapter]] = None
    image_cost_cap_usd: float = 2.0

    # Boot
    auto_boot: bool = True
    strict_sanity_checks: bool = False

    # Paths (derived)
    @property
    def vault_dir(self) -> Path:
        return self.storage_root / "vault"

    @property
    def nonce_store_path(self) -> Path:
        return self.storage_root / "security" / "nonces.json"

    @property
    def kill_switch_path(self) -> Path:
        return self.storage_root / "security" / "kill_switch.flag"

    @property
    def error_ledger_path(self) -> Path:
        return self.storage_root / "evolution" / "errors.jsonl"

    @property
    def deploy_ledger_path(self) -> Path:
        return self.storage_root / "deploy" / "deploy_log.jsonl"

    @property
    def llm_audit_path(self) -> Path:
        return self.storage_root / "external" / "llm_audit.jsonl"


# ============================================================
# 2. APEX FACTORY (main facade)
# ============================================================

class ApexFactory:
    """
    Facade tối thượng. C2 chỉ tương tác với class này.

    Typical usage:
        factory = ApexFactory(
            component_catalog=my_catalog,
            token_registry=my_tokens,
            config=ApexFactoryConfig(...),
        )
        factory.boot()
        artifact = factory.build_web("Tôi cần landing page AI course...")
        if artifact.is_success():
            token = factory.c2_issue_token("deploy", "deploy:vercel:my-app")
            deploy_result = factory.deploy(deploy_req, token)
    """

    VERSION = APEX_FACTORY_VERSION
    CODENAME = APEX_FACTORY_CODENAME

    def __init__(
        self,
        *,
        component_catalog: ComponentCatalog,
        token_registry: TokenRegistry,
        config: Optional[ApexFactoryConfig] = None,
        project_id: Optional[str] = None,
    ):
        self.config = config or ApexFactoryConfig()
        self.catalog = component_catalog
        self.registry = token_registry
        self.project_id = project_id or f"proj_{hash(id(self)) & 0xFFFFFF:06x}"

        # Ensure storage dirs
        for p in [
            self.config.vault_dir, self.config.nonce_store_path.parent,
            self.config.kill_switch_path.parent, self.config.error_ledger_path.parent,
            self.config.deploy_ledger_path.parent, self.config.llm_audit_path.parent,
        ]:
            p.mkdir(parents=True, exist_ok=True)

        # Security core (lazy)
        self._token_signer: Optional[CapabilityTokenSigner] = None
        self._capability_gate: Optional[CapabilityGate] = None
        self.kill_switch = KillSwitch(self.config.kill_switch_path)
        self.nonce_store = NonceStore(self.config.nonce_store_path)

        # Try init signer (requires C2_MASTER_SECRET env)
        try:
            self._token_signer = CapabilityTokenSigner()
            self._capability_gate = CapabilityGate(
                self._token_signer, self.nonce_store,
            )
        except RuntimeError as e:
            self._init_signer_error = str(e)
        else:
            self._init_signer_error = None

        # Domain registry
        self.domain_registry = DomainRegistry()
        self.domain_registry.enable(self.config.default_domain)

        # Project lineage
        self.lineage = ProjectLineage(project_id=self.project_id)

        # Ledgers
        self.error_ledger = ErrorLedgerV6(
            self.config.error_ledger_path,
            RotationPolicy(),
        )
        self.deploy_ledger = DeployLedger(self.config.deploy_ledger_path)

        # LLM Broker
        self._llm_broker: Optional[LLMBroker] = self._init_llm_broker()

        # Factories (lazy)
        self._web_factory: Optional[WebFactory] = None
        self._mobile_factory: Optional[MobileFactory] = None
        self._video_factory: Optional[VideoFactory] = None
        self._image_factory: Optional[ImageFactory] = None
        self._deploy_adapter: Optional[DeployAdapter] = None
        self._hot_inject_engine: Optional[HotInjectEngine] = None

        # State
        self._booted: bool = False
        self._boot_report: Optional[Dict[str, Any]] = None

        if self.config.auto_boot:
            self.boot()

    # ============================================================
    # 3. BOOT + HEALTH
    # ============================================================

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def boot(self) -> Dict[str, Any]:
        """Self-check toàn hệ thống. Gọi tự động nếu auto_boot=True."""
        checks: Dict[str, Any] = {}

        # Foundation
        checks["ontology_ui"] = all(ontology_ui_sanity_check().values())
        checks["ontology_media"] = all(ontology_media_sanity_check().values())
        checks["composition_rules"] = all(composition_rules_sanity_check().values())
        checks["principles_v6"] = all(principles_v6_sanity_check().values())

        # Security
        checks["capability_signer_ready"] = self._capability_gate is not None
        checks["kill_switch_inactive"] = not self.kill_switch.is_activated()

        # Catalog + registry
        catalog_violations = self.catalog.validate_all(self.registry)
        checks["catalog_valid"] = len(catalog_violations) == 0
        if catalog_violations:
            checks["catalog_violations_count"] = len(catalog_violations)

        # LLM broker
        checks["llm_broker_initialized"] = self._llm_broker is not None
        if self._llm_broker:
            checks["llm_adapters_available"] = len(self._llm_broker.list_available())

        # Overall
        hard_fail_keys = [
            "ontology_ui", "ontology_media", "composition_rules",
            "principles_v6", "kill_switch_inactive",
        ]
        all_hard_ok = all(checks.get(k, False) for k in hard_fail_keys)

        report = {
            "version": self.VERSION,
            "codename": self.CODENAME,
            "booted_at_utc": _now_iso(),
            "project_id": self.project_id,
            "checks": checks,
            "boot_success": all_hard_ok,
            "warnings": [],
        }

        if self._init_signer_error:
            report["warnings"].append(
                f"CapabilityTokenSigner not initialized: {self._init_signer_error}. "
                f"Set C2_MASTER_SECRET env var to enable signing."
            )
        if catalog_violations:
            report["warnings"].append(
                f"ComponentCatalog có {len(catalog_violations)} vi phạm NT11 - "
                f"xem full: self.catalog.validate_all(self.registry)"
            )

        self._booted = report["boot_success"]
        self._boot_report = report

        if self.config.strict_sanity_checks and not report["boot_success"]:
            raise RuntimeError(
                f"APEX FACTORY boot failed: {report['warnings']}"
            )

        return report

    def get_health_snapshot(self) -> Dict[str, Any]:
        """Snapshot toàn hệ thống cho dashboard / CLI."""
        return {
            "version": self.VERSION,
            "codename": self.CODENAME,
            "booted": self._booted,
            "project_id": self.project_id,
            "kill_switch_active": self.kill_switch.is_activated(),
            "capability_signer_ready": self._capability_gate is not None,
            "storage_root": str(self.config.storage_root),

            "catalog": {
                "size": self.catalog.size(),
                "fingerprint": self.catalog.fingerprint()[:16],
            },
            "token_registry": {
                **self.registry.summary(),
                "fingerprint": self.registry.fingerprint()[:16],
            },

            "lineage": self.lineage.summary(),

            "domain_registry": self.domain_registry.summary(),

            "error_ledger": self.error_ledger.summary(),

            "llm_broker": (
                self._llm_broker.summary() if self._llm_broker
                else {"available": False}
            ),

            "snapshot_at_utc": _now_iso(),
        }

    # ============================================================
    # 4. LLM BROKER INIT
    # ============================================================

    def _init_llm_broker(self) -> Optional[LLMBroker]:
        adapters = self.config.llm_adapters
        if adapters is None:
            # Default: từ env variables
            adapters = self._default_llm_adapters()
        if not adapters:
            return None

        broker_config = BrokerConfig(
            cost_cap_usd_per_run=self.config.llm_cost_cap_usd,
            audit_path=(
                self.config.llm_audit_path if self.config.llm_audit_enabled else None
            ),
        )
        return LLMBroker(
            adapters=adapters,
            config=broker_config,
            schema_guard=SchemaGuard(),
        )

    @staticmethod
    def _default_llm_adapters() -> List[LLMAdapter]:
        import os
        adapters: List[LLMAdapter] = []
        # OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            adapters.append(OpenAIAdapter(
                api_key=os.environ["OPENAI_API_KEY"],
            ))
        # Anthropic
        if os.environ.get("ANTHROPIC_API_KEY"):
            adapters.append(AnthropicAdapter(
                api_key=os.environ["ANTHROPIC_API_KEY"],
            ))
        # Gemini
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            adapters.append(GeminiAdapter(api_key=key))
        # Ollama local (optional)
        if os.environ.get("OLLAMA_ENABLED", "").lower() in ("1", "true", "yes"):
            adapters.append(OllamaAdapter())
        # Always có mock làm fallback cuối
        adapters.append(MockAdapter())
        return adapters

    # ============================================================
    # 5. FACTORY ACCESSORS (lazy init)
    # ============================================================

    @property
    def web(self) -> WebFactory:
        if self._web_factory is None:
            self._web_factory = WebFactory(
                component_catalog=self.catalog,
                token_registry=self.registry,
                config=self.config.web_config or WebFactoryConfig(
                    project_id=self.project_id,
                ),
                llm_broker=self._llm_broker,
                project_lineage=self.lineage,
            )
        return self._web_factory

    @property
    def mobile(self) -> MobileFactory:
        if self._mobile_factory is None:
            self._mobile_factory = MobileFactory(
                component_catalog=self.catalog,
                token_registry=self.registry,
                config=MobileFactoryConfig(),
            )
        return self._mobile_factory

    @property
    def video(self) -> VideoFactory:
        if self._video_factory is None:
            self._video_factory = VideoFactory(VideoFactoryConfig())
        return self._video_factory

    @property
    def image(self) -> ImageFactory:
        if self._image_factory is None:
            adapters = self.config.image_adapters or [MockImageProvider()]
            self._image_factory = ImageFactory(
                adapters=adapters,
                config=ImageFactoryConfig(
                    cost_cap_usd_per_batch=self.config.image_cost_cap_usd,
                ),
            )
        return self._image_factory

    @property
    def deploy_adapter(self) -> DeployAdapter:
        if self._deploy_adapter is None:
            if self._capability_gate is None:
                raise RuntimeError(
                    "Deploy requires CapabilityGate - set C2_MASTER_SECRET"
                )
            self._deploy_adapter = DeployAdapter(
                capability_gate=self._capability_gate,
                kill_switch=self.kill_switch,
                ledger=self.deploy_ledger,
            )
        return self._deploy_adapter

    @property
    def hot_inject_engine(self) -> HotInjectEngine:
        if self._hot_inject_engine is None:
            if self._capability_gate is None:
                raise RuntimeError(
                    "HotInject requires CapabilityGate - set C2_MASTER_SECRET"
                )
            emitter = ReactEmitter(
                self.catalog, self.registry,
                EmitConfig(app_name="apex-hot-inject"),
            )
            self._hot_inject_engine = HotInjectEngine(
                surgeon=ASTSurgeonV6(self.catalog),
                emitter=emitter,
                ledger=self.error_ledger,
                capability_gate=self._capability_gate,
                kill_switch=self.kill_switch,
                lineage=self.lineage,
                component_catalog=self.catalog,
                token_registry=self.registry,
            )
        return self._hot_inject_engine

    # ============================================================
    # 6. HIGH-LEVEL BUILD METHODS
    # ============================================================

    @enforce_principle_v6(PrincipleV6.NT1_MULTI_AXIS_CONVERGENCE)
    def build_web(
        self, raw_brief: str, c2_signal: Optional[str] = None,
    ) -> BuildArtifact:
        """Build web project end-to-end."""
        return self.web.build(raw_brief, c2_signal=c2_signal)

    def build_mobile_from_graph(self, graph: DesignGraph) -> Any:
        """Build React Native app từ DesignGraph."""
        return self.mobile.build_from_graph(graph)

    def build_video(self, scene: SceneGraph) -> Any:
        """Build video project từ SceneGraph (Remotion)."""
        return self.video.build_from_scene(scene)

    def generate_image(self, request: ImageGenRequest) -> ImageGenResult:
        """Sinh ảnh qua ImageFactory."""
        return self.image.generate(request)

    # ============================================================
    # 7. C2 COMMANDS (Capability Token required)
    # ============================================================

    def c2_issue_token(
        self,
        scope: str,
        target_resource: str,
        ttl_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CapabilityToken]:
        """C2 ký token mới."""
        if self._token_signer is None:
            return None
        if scope not in ALLOWED_SCOPES and scope not in (
            "hot_inject", "deploy", "override_decision",
        ):
            raise ValueError(
                f"Scope '{scope}' not allowed. "
                f"Add vào ALLOWED_SCOPES hoặc dùng scope v6 (hot_inject/deploy/override_decision)"
            )
        return self._token_signer.sign(
            scope=scope,
            target_resource=target_resource,
            ttl_seconds=ttl_seconds,
            metadata=metadata,
        )

    def c2_deploy(
        self, request: DeployRequest, token: CapabilityToken,
    ) -> DeployResult:
        """C2 deploy. Token BẮT BUỘC."""
        return self.deploy_adapter.deploy(request, token)

    def c2_hot_inject(
        self, request: InjectRequest, token: CapabilityToken,
    ) -> InjectResult:
        """C2 hot-inject patch. Token BẮT BUỘC."""
        return self.hot_inject_engine.inject(request, token)

    def c2_kill_switch(self, activate: bool, reason: str = "") -> Dict[str, Any]:
        """Kick-stop toàn hệ thống."""
        if activate:
            self.kill_switch.activate(reason)
        else:
            self.kill_switch.deactivate()
        return {
            "active": self.kill_switch.is_activated(),
            "reason": reason,
            "timestamp": _now_iso(),
        }

    # ============================================================
    # 8. EXPORT / IMPORT
    # ============================================================

    def export_state(self, output_path: Path) -> Path:
        """Export health snapshot + lineage ra file JSON."""
        snapshot = self.get_health_snapshot()
        snapshot["lineage_detail"] = {
            sid: snap.to_dict()
            for sid, snap in self.lineage.snapshots.items()
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return output_path

    def __repr__(self) -> str:
        return (
            f"<ApexFactory v{self.VERSION} "
            f"project={self.project_id} "
            f"booted={self._booted} "
            f"catalog_size={self.catalog.size()} "
            f"kill_switch={'ON' if self.kill_switch.is_activated() else 'OFF'}>"
        )


# ============================================================
# 9. SANITY CHECK
# ============================================================

def apex_factory_sanity_check() -> Dict[str, bool]:
    import os
    import tempfile

    from apex_core.foundation.ontology_ui import (
        ColorToken,
        TokenRole,
    )

    checks: Dict[str, bool] = {}
    tmp = Path(tempfile.mkdtemp(prefix="apex_factory_"))

    if not os.environ.get("C2_MASTER_SECRET"):
        os.environ["C2_MASTER_SECRET"] = "test" * 16

    catalog = ComponentCatalog()
    registry = TokenRegistry()
    registry.add(ColorToken(
        token_id="c.primary", value="#2563EB", role=TokenRole.PRIMARY,
    ))
    registry.freeze()

    factory = ApexFactory(
        component_catalog=catalog,
        token_registry=registry,
        config=ApexFactoryConfig(
            storage_root=tmp,
            auto_boot=True,
            strict_sanity_checks=False,
        ),
    )

    checks["factory_booted"] = factory._booted
    checks["catalog_accessible"] = factory.catalog.size() >= 0
    checks["registry_frozen"] = factory.registry.is_frozen

    # Health snapshot
    snap = factory.get_health_snapshot()
    checks["snapshot_has_version"] = snap.get("version") == APEX_FACTORY_VERSION
    checks["snapshot_has_lineage"] = "lineage" in snap

    # Build web (empty catalog → placeholder)
    artifact = factory.build_web(
        "Landing page tối giản có navbar hero cta footer, bundle 300kb"
    )
    checks["web_build_ok"] = artifact is not None
    checks["web_build_has_variants"] = len(artifact.variants_evaluated) >= 1

    # Image
    from apex_core.factories.image_factory import ImageGenRequest, ImageProvider
    img_result = factory.generate_image(ImageGenRequest(
        prompt="A coffee shop", provider=ImageProvider.MOCK,
    ))
    checks["image_gen_ok"] = img_result.success

    # Token issuance
    token = factory.c2_issue_token(
        scope="deploy",
        target_resource="deploy:vercel:test",
        ttl_seconds=600,
    )
    checks["token_issued"] = token is not None

    # Kill switch toggle
    factory.c2_kill_switch(True, "test")
    checks["kill_switch_activated"] = factory.kill_switch.is_activated()
    factory.c2_kill_switch(False)
    checks["kill_switch_deactivated"] = not factory.kill_switch.is_activated()

    # Export state
    export_path = factory.export_state(tmp / "state.json")
    checks["export_file_created"] = export_path.exists()
    checks["export_valid_json"] = bool(
        json.loads(export_path.read_text(encoding="utf-8"))
    )

    return checks


__all__ = [
    "APEX_FACTORY_VERSION", "APEX_FACTORY_CODENAME", "BANNER",
    "ApexFactoryConfig",
    "ApexFactory",
    "apex_factory_sanity_check",
]
