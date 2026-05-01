"""
APEX FACTORY v6.0 - Foundation Extension
File: project_snapshot.py

Mục đích: ProjectSnapshot - bất biến, SHA-256 protected. Thay thế vai trò
          của DrawSnapshot (v5.0) khi hệ thống pivot sang sản xuất.

Một ProjectSnapshot = 1 "kết quả của Xưởng" tại thời điểm t:
    - Web project    → chứa DesignGraph + TokenRegistry fingerprint
    - App project    → chứa DesignGraph + mobile-specific metadata
    - Video project  → chứa SceneGraph
    - Image/Mixed    → kết hợp

Bất biến sau khi tạo. Mọi thay đổi = tạo snapshot mới với SHA khác.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apex_core.foundation.ontology_media import SceneGraph
from apex_core.foundation.ui_ir import DesignGraph

# ============================================================
# 0. VERSION
# ============================================================

PROJECT_SNAPSHOT_VERSION = "6.0.0"
PROJECT_SNAPSHOT_SCHEMA = "apex.factory.project-snapshot/v6"


# ============================================================
# 1. ENUMS
# ============================================================

class ProjectStage(str, Enum):
    """Vòng đời của 1 project snapshot."""
    DRAFT = "draft"                 # Mới sinh, chưa qua Radar
    RADAR_SCORED = "radar_scored"   # Đã có Radar 4D score
    UNDER_REVIEW = "under_review"   # Round Table đang xem
    APPROVED = "approved"           # Pass Round Table + có C2 token
    DEPLOYED = "deployed"           # Đã publish thực tế
    REJECTED = "rejected"           # Bị Round Table từ chối
    SUPERSEDED = "superseded"       # Có snapshot mới tốt hơn thay thế


class ArtifactKind(str, Enum):
    """Các loại artifact kèm theo snapshot."""
    SOURCE_CODE = "source_code"     # zip source
    BUILD_OUTPUT = "build_output"   # dist/ folder
    VIDEO_FILE = "video_file"       # .mp4 output
    IMAGE_FILE = "image_file"       # .png/.jpg
    LIGHTHOUSE = "lighthouse"       # JSON report
    STORYBOOK = "storybook"         # Storybook static build
    PREVIEW_URL = "preview_url"     # deployed preview


# ============================================================
# 2. ARTIFACT REFERENCE
# ============================================================

@dataclass(frozen=True)
class ArtifactRef:
    """Reference đến 1 output artifact."""
    artifact_id: str
    kind: ArtifactKind
    location: str                       # path / URL / S3 key
    size_bytes: int = 0
    content_hash: str = ""              # SHA-256 of artifact content
    produced_at_utc: str = ""
    producer: str = ""                  # brain_id or external tool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind.value,
            "location": self.location,
            "size_bytes": self.size_bytes,
            "content_hash": self.content_hash,
            "produced_at_utc": self.produced_at_utc,
            "producer": self.producer,
        }


# ============================================================
# 3. RADAR 4D SCORE EMBED (placeholder schema - chi tiết ở Phase 2)
# ============================================================

@dataclass(frozen=True)
class Radar4DEmbed:
    """Snapshot điểm Radar 4D tại thời điểm đo."""
    speed_score: float                  # X axis
    footprint_score: float              # Y axis
    stability_score: float              # Z axis
    cleanliness_score: float            # T axis
    composite: float                    # weighted sum
    mdl_penalty: float = 0.0
    measured_at_utc: str = ""

    def __post_init__(self):
        for name, val in (
            ("speed_score", self.speed_score),
            ("footprint_score", self.footprint_score),
            ("stability_score", self.stability_score),
            ("cleanliness_score", self.cleanliness_score),
            ("composite", self.composite),
        ):
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name}={val} out of [0,1]")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# 4. PROJECT SNAPSHOT (immutable)
# ============================================================

@dataclass(frozen=True)
class ProjectSnapshot:
    """
    Snapshot bất biến của 1 project tại thời điểm t.
    Giống DrawSnapshot v5.0: SHA-256 protected, append-only.
    """
    # --- Identity ---
    project_id: str
    snapshot_id: str
    version_label: str                  # "v1", "v1.2", "variant-b-rev3"
    parent_snapshot_id: Optional[str]   # lineage

    # --- Domain ---
    domain: str                         # DomainType.value
    stage: str                          # ProjectStage.value

    # --- Brief (intent gốc) ---
    brief_hash: str                     # SHA-256 của BriefSpec gốc
    brief_summary: str = ""             # tóm tắt text ≤ 500 chars

    # --- Body - chỉ 1 trong 3 non-empty tại mỗi snapshot ---
    design_graph_dict: Optional[Dict[str, Any]] = None  # serialize DesignGraph
    scene_graph_dict: Optional[Dict[str, Any]] = None   # serialize SceneGraph
    mixed_graph_dicts: Tuple[Dict[str, Any], ...] = ()  # cho MIXED

    # --- Fingerprints của registry (FK immutable) ---
    token_registry_fingerprint: str = ""
    component_catalog_fingerprint: str = ""

    # --- Radar 4D score (nếu đã đo) ---
    radar_4d: Optional[Radar4DEmbed] = None

    # --- Round Table verdict (nếu đã qua) ---
    round_table_summary: Optional[Dict[str, Any]] = None

    # --- Artifacts ---
    artifacts: Tuple[ArtifactRef, ...] = ()

    # --- Meta ---
    created_at_utc: str = ""
    created_by: str = "system"          # "system" | "B6.commander" | "external_llm"
    tags: Tuple[str, ...] = ()

    # --- Integrity ---
    checksum_sha256: str = ""

    def __post_init__(self):
        if not self.created_at_utc:
            object.__setattr__(
                self, "created_at_utc",
                datetime.now(timezone.utc).isoformat()
            )
        if not self.checksum_sha256:
            object.__setattr__(self, "checksum_sha256", self._compute_checksum())

    def _compute_checksum(self) -> str:
        payload = {
            "project_id": self.project_id,
            "snapshot_id": self.snapshot_id,
            "version_label": self.version_label,
            "parent_snapshot_id": self.parent_snapshot_id,
            "domain": self.domain,
            "stage": self.stage,
            "brief_hash": self.brief_hash,
            "design_graph_dict": self.design_graph_dict,
            "scene_graph_dict": self.scene_graph_dict,
            "mixed_graph_dicts": list(self.mixed_graph_dicts),
            "token_registry_fingerprint": self.token_registry_fingerprint,
            "component_catalog_fingerprint": self.component_catalog_fingerprint,
            "radar_4d": self.radar_4d.to_dict() if self.radar_4d else None,
            "round_table_summary": self.round_table_summary,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "created_at_utc": self.created_at_utc,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
            .encode("utf-8")
        ).hexdigest()

    def verify_integrity(self) -> bool:
        """Re-compute checksum và so sánh - nếu ai sửa thì sai."""
        return self._compute_checksum() == self.checksum_sha256

    # --------- Derived helpers ---------
    def has_design_graph(self) -> bool:
        return self.design_graph_dict is not None

    def has_scene_graph(self) -> bool:
        return self.scene_graph_dict is not None

    def is_renderable(self) -> bool:
        return self.has_design_graph() or self.has_scene_graph() or bool(self.mixed_graph_dicts)

    def load_design_graph(self) -> Optional[DesignGraph]:
        if self.design_graph_dict is None:
            return None
        return DesignGraph.from_dict(self.design_graph_dict)

    # SceneGraph không có classmethod from_dict chi tiết ở Phase 0 - trả raw dict
    def load_scene_graph_dict(self) -> Optional[Dict[str, Any]]:
        return self.scene_graph_dict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": PROJECT_SNAPSHOT_SCHEMA,
            "version": PROJECT_SNAPSHOT_VERSION,
            "project_id": self.project_id,
            "snapshot_id": self.snapshot_id,
            "version_label": self.version_label,
            "parent_snapshot_id": self.parent_snapshot_id,
            "domain": self.domain,
            "stage": self.stage,
            "brief_hash": self.brief_hash,
            "brief_summary": self.brief_summary,
            "design_graph_dict": self.design_graph_dict,
            "scene_graph_dict": self.scene_graph_dict,
            "mixed_graph_dicts": list(self.mixed_graph_dicts),
            "token_registry_fingerprint": self.token_registry_fingerprint,
            "component_catalog_fingerprint": self.component_catalog_fingerprint,
            "radar_4d": self.radar_4d.to_dict() if self.radar_4d else None,
            "round_table_summary": self.round_table_summary,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "created_at_utc": self.created_at_utc,
            "created_by": self.created_by,
            "tags": list(self.tags),
            "checksum_sha256": self.checksum_sha256,
        }


# ============================================================
# 5. PROJECT LINEAGE - chuỗi snapshot theo thời gian
# ============================================================

@dataclass
class ProjectLineage:
    """
    Quản lý lineage cho 1 project: v1 -> v1.1 -> v1.2 ...
    Bản chất là DAG append-only theo parent_snapshot_id.
    """
    project_id: str
    snapshots: Dict[str, ProjectSnapshot] = field(default_factory=dict)
    head_snapshot_id: Optional[str] = None      # snapshot hiện tại ở trạng thái APPROVED/DEPLOYED

    def append(self, snapshot: ProjectSnapshot) -> None:
        if snapshot.project_id != self.project_id:
            raise ValueError(
                f"Snapshot project_id mismatch: {snapshot.project_id} vs {self.project_id}"
            )
        if snapshot.snapshot_id in self.snapshots:
            raise ValueError(f"Duplicate snapshot_id: {snapshot.snapshot_id}")
        if snapshot.parent_snapshot_id and snapshot.parent_snapshot_id not in self.snapshots:
            raise ValueError(
                f"Parent snapshot not found: {snapshot.parent_snapshot_id}"
            )
        if not snapshot.verify_integrity():
            raise ValueError(f"Snapshot integrity check failed: {snapshot.snapshot_id}")
        self.snapshots[snapshot.snapshot_id] = snapshot

    def set_head(self, snapshot_id: str) -> None:
        if snapshot_id not in self.snapshots:
            raise KeyError(snapshot_id)
        self.head_snapshot_id = snapshot_id

    def get_head(self) -> Optional[ProjectSnapshot]:
        if self.head_snapshot_id is None:
            return None
        return self.snapshots.get(self.head_snapshot_id)

    def trace_lineage(self, snapshot_id: str) -> List[ProjectSnapshot]:
        """Truy ngược từ snapshot_id về gốc qua parent_snapshot_id."""
        chain: List[ProjectSnapshot] = []
        current_id: Optional[str] = snapshot_id
        seen: set = set()
        while current_id:
            if current_id in seen:
                break           # cycle safety
            seen.add(current_id)
            snap = self.snapshots.get(current_id)
            if snap is None:
                break
            chain.append(snap)
            current_id = snap.parent_snapshot_id
        return chain

    def get_children_of(self, snapshot_id: str) -> List[ProjectSnapshot]:
        return [
            s for s in self.snapshots.values()
            if s.parent_snapshot_id == snapshot_id
        ]

    def latest_by_stage(self, stage: ProjectStage) -> Optional[ProjectSnapshot]:
        candidates = [s for s in self.snapshots.values() if s.stage == stage.value]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.created_at_utc)

    def summary(self) -> Dict[str, Any]:
        stage_counts: Dict[str, int] = {}
        for s in self.snapshots.values():
            stage_counts[s.stage] = stage_counts.get(s.stage, 0) + 1
        return {
            "project_id": self.project_id,
            "total_snapshots": len(self.snapshots),
            "head_snapshot_id": self.head_snapshot_id,
            "stage_counts": stage_counts,
        }


# ============================================================
# 6. FACTORY FUNCTIONS
# ============================================================

def build_snapshot_from_design_graph(
    *,
    project_id: str,
    snapshot_id: str,
    version_label: str,
    domain: str,
    graph: DesignGraph,
    brief_hash: str,
    brief_summary: str = "",
    parent_snapshot_id: Optional[str] = None,
    token_registry_fingerprint: str = "",
    component_catalog_fingerprint: str = "",
    stage: ProjectStage = ProjectStage.DRAFT,
    created_by: str = "system",
    tags: Sequence[str] = (),
) -> ProjectSnapshot:
    return ProjectSnapshot(
        project_id=project_id,
        snapshot_id=snapshot_id,
        version_label=version_label,
        parent_snapshot_id=parent_snapshot_id,
        domain=domain,
        stage=stage.value,
        brief_hash=brief_hash,
        brief_summary=brief_summary[:500],
        design_graph_dict=graph.to_dict(),
        scene_graph_dict=None,
        mixed_graph_dicts=(),
        token_registry_fingerprint=token_registry_fingerprint,
        component_catalog_fingerprint=component_catalog_fingerprint,
        created_by=created_by,
        tags=tuple(tags),
    )


def build_snapshot_from_scene_graph(
    *,
    project_id: str,
    snapshot_id: str,
    version_label: str,
    domain: str,
    scene: SceneGraph,
    brief_hash: str,
    brief_summary: str = "",
    parent_snapshot_id: Optional[str] = None,
    stage: ProjectStage = ProjectStage.DRAFT,
    created_by: str = "system",
    tags: Sequence[str] = (),
) -> ProjectSnapshot:
    return ProjectSnapshot(
        project_id=project_id,
        snapshot_id=snapshot_id,
        version_label=version_label,
        parent_snapshot_id=parent_snapshot_id,
        domain=domain,
        stage=stage.value,
        brief_hash=brief_hash,
        brief_summary=brief_summary[:500],
        design_graph_dict=None,
        scene_graph_dict=scene.to_dict(),
        mixed_graph_dicts=(),
        created_by=created_by,
        tags=tuple(tags),
    )


# ============================================================
# 7. SANITY CHECK
# ============================================================

def project_snapshot_sanity_check() -> Dict[str, bool]:
    from apex_core.foundation.ontology_media import (
        RESOLUTION_FHD,
        CameraMotion,
        MediaDomain,
        SceneGraph,
        ShotSpec,
    )
    from apex_core.foundation.ui_ir import DesignNode, RenderTarget

    checks: Dict[str, bool] = {}

    # Case 1: Snapshot từ DesignGraph
    try:
        g = DesignGraph(graph_id="g", target=RenderTarget.REACT, root_id="r")
        g.add_node(DesignNode(node_id="r", component_id="atom.box"))
        snap = build_snapshot_from_design_graph(
            project_id="p1",
            snapshot_id="s1",
            version_label="v1",
            domain="web",
            graph=g,
            brief_hash="abc123",
        )
        checks["snap_build_ok"] = snap.verify_integrity()
        checks["snap_has_design_graph"] = snap.has_design_graph()
    except Exception:
        checks["snap_build_ok"] = False

    # Case 2: Lineage append
    try:
        lineage = ProjectLineage(project_id="p1")
        lineage.append(snap)
        snap2 = build_snapshot_from_design_graph(
            project_id="p1",
            snapshot_id="s2",
            version_label="v1.1",
            domain="web",
            graph=g,
            brief_hash="abc123",
            parent_snapshot_id="s1",
        )
        lineage.append(snap2)
        chain = lineage.trace_lineage("s2")
        checks["lineage_chain"] = len(chain) == 2 and chain[-1].snapshot_id == "s1"
    except Exception:
        checks["lineage_chain"] = False

    # Case 3: Integrity tampering detection
    try:
        # Can't mutate frozen dataclass directly; simulate bằng cách tạo mới với checksum sai
        bad = ProjectSnapshot(
            project_id="p1",
            snapshot_id="s_bad",
            version_label="v1",
            parent_snapshot_id=None,
            domain="web",
            stage=ProjectStage.DRAFT.value,
            brief_hash="abc",
            checksum_sha256="deadbeef" * 8,   # sai
        )
        # verify_integrity phải trả False vì checksum không khớp payload
        checks["tamper_detected"] = bad.verify_integrity() is False
    except Exception:
        checks["tamper_detected"] = False

    # Case 4: Scene graph snapshot
    try:
        scene = SceneGraph(
            scene_id="sc",
            domain=MediaDomain.VIDEO,
            canvas_resolution=RESOLUTION_FHD,
            target_duration_ms=1000,
        )
        scene.add_shot(ShotSpec(
            shot_id="sh",
            duration_ms=1000,
            fps=30,
            camera_motion=CameraMotion.STATIC,
            resolution=RESOLUTION_FHD,
        ))
        scene.append_shot_to_track("video_main", "sh")
        vid_snap = build_snapshot_from_scene_graph(
            project_id="v1",
            snapshot_id="vs1",
            version_label="v1",
            domain="video",
            scene=scene,
            brief_hash="xyz",
        )
        checks["video_snap_ok"] = vid_snap.has_scene_graph() and vid_snap.verify_integrity()
    except Exception:
        checks["video_snap_ok"] = False

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "PROJECT_SNAPSHOT_VERSION",
    "PROJECT_SNAPSHOT_SCHEMA",
    "ProjectStage",
    "ArtifactKind",
    "ArtifactRef",
    "Radar4DEmbed",
    "ProjectSnapshot",
    "ProjectLineage",
    "build_snapshot_from_design_graph",
    "build_snapshot_from_scene_graph",
    "project_snapshot_sanity_check",
]
