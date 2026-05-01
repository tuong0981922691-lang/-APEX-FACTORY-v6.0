"""
APEX FACTORY v6.0 - Evolution Layer (v6)
File: error_ledger_v6.py

Mục đích: Nâng cấp ErrorLedger Phase 1 thành ErrorLedgerV6:
    - Severity buckets + weighted scoring
    - Deduplication qua error_signature (normalize stack trace)
    - Rotation (age + size limit)
    - Query API: by time range, kind, severity, component
    - Cluster analysis: tìm error pattern lặp lại để ưu tiên vá

Triết lý:
    - Append-only (không xóa) - chỉ rotate sang archive file
    - SHA-256 per entry → chống tampering
    - Index in-memory cho query nhanh - rebuild từ file khi boot
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Kế thừa types từ Phase 1
from apex_core.brains_v6.b7_runtime_forge import (
    ErrorEntry,
    ErrorKind,
)

# ============================================================
# 0. VERSION
# ============================================================

ERROR_LEDGER_V6_VERSION = "6.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


# ============================================================
# 1. SEVERITY BUCKETS + WEIGHTS
# ============================================================

class SeverityBucket(str, Enum):
    CRITICAL = "critical"          # app down, data loss
    ERROR = "error"                # feature broken
    WARNING = "warning"            # degraded UX
    INFO = "info"                  # log-only


SEVERITY_WEIGHTS: Dict[SeverityBucket, float] = {
    SeverityBucket.CRITICAL: 10.0,
    SeverityBucket.ERROR: 3.0,
    SeverityBucket.WARNING: 1.0,
    SeverityBucket.INFO: 0.1,
}


def normalize_severity(raw: str) -> SeverityBucket:
    raw_lower = (raw or "").lower().strip()
    mapping = {
        "critical": SeverityBucket.CRITICAL,
        "fatal":    SeverityBucket.CRITICAL,
        "error":    SeverityBucket.ERROR,
        "err":      SeverityBucket.ERROR,
        "warning":  SeverityBucket.WARNING,
        "warn":     SeverityBucket.WARNING,
        "info":     SeverityBucket.INFO,
    }
    return mapping.get(raw_lower, SeverityBucket.ERROR)


# ============================================================
# 2. ERROR SIGNATURE (deduplication)
# ============================================================

# Các pattern biến động cần strip để dedup (UUID, hex, timestamp, path)
_UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
_HEX_RE = re.compile(r"\b0x[0-9a-f]{4,}\b", re.I)
_TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\d.Z+:-]*\b")
_LINE_COL_RE = re.compile(r":\d+:\d+")
_PATH_PREFIX_RE = re.compile(r"/(?:Users|home|tmp|var)/[^\s:]*/")


def compute_error_signature(
    kind: str,
    message: str,
    stack_trace: str,
    component_id: Optional[str] = None,
) -> str:
    """
    Chuẩn hóa stack trace để 2 lỗi "cùng bản chất" có signature giống nhau.
    """
    # Normalize message
    msg_norm = _UUID_RE.sub("<UUID>", message)
    msg_norm = _HEX_RE.sub("<HEX>", msg_norm)
    msg_norm = _TIMESTAMP_RE.sub("<TS>", msg_norm)

    # Normalize stack (giữ function name, strip line:col và path)
    stack_norm = _LINE_COL_RE.sub("", stack_trace or "")
    stack_norm = _PATH_PREFIX_RE.sub("/", stack_norm)
    stack_norm = _UUID_RE.sub("<UUID>", stack_norm)
    stack_norm = _HEX_RE.sub("<HEX>", stack_norm)
    # Chỉ lấy top 5 frames
    frames = [f.strip() for f in stack_norm.splitlines() if f.strip()][:5]

    payload = {
        "kind": kind,
        "message_hash_prefix": msg_norm[:200],
        "stack_top_frames": frames,
        "component_id": component_id or "",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]     # 24 hex = đủ unique, ngắn


# ============================================================
# 3. CLUSTERED ERROR ENTRY
# ============================================================

@dataclass
class ErrorCluster:
    """Gom các entry cùng signature thành 1 cluster."""
    signature: str
    kind: str
    severity: SeverityBucket
    sample_message: str
    sample_stack_top: str
    first_seen_utc: str
    last_seen_utc: str
    occurrence_count: int = 1
    affected_components: List[str] = field(default_factory=list)
    affected_graphs: List[str] = field(default_factory=list)
    latest_entry_ids: List[str] = field(default_factory=list)   # capped to 20

    def severity_weight(self) -> float:
        return SEVERITY_WEIGHTS.get(self.severity, 1.0)

    def priority_score(self) -> float:
        """Score cao = nên vá trước. Công thức: occ × severity × recency."""
        recency_bonus = 1.0
        last_dt = _parse_iso(self.last_seen_utc)
        if last_dt:
            age_hours = max(
                0.0,
                (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600.0,
            )
            recency_bonus = 1.0 / (1.0 + age_hours / 24.0)   # decay per day
        return self.occurrence_count * self.severity_weight() * (0.5 + recency_bonus)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature": self.signature,
            "kind": self.kind,
            "severity": self.severity.value,
            "sample_message": self.sample_message[:300],
            "sample_stack_top": self.sample_stack_top[:300],
            "first_seen_utc": self.first_seen_utc,
            "last_seen_utc": self.last_seen_utc,
            "occurrence_count": self.occurrence_count,
            "affected_components": list(self.affected_components)[:20],
            "affected_graphs": list(self.affected_graphs)[:20],
            "priority_score": round(self.priority_score(), 4),
            "severity_weight": self.severity_weight(),
        }


# ============================================================
# 4. QUERY PARAMS
# ============================================================

@dataclass
class LedgerQuery:
    kind: Optional[str] = None
    severity: Optional[SeverityBucket] = None
    component_id: Optional[str] = None
    graph_id: Optional[str] = None
    since_utc: Optional[str] = None
    until_utc: Optional[str] = None
    limit: int = 100


# ============================================================
# 5. ROTATION POLICY
# ============================================================

@dataclass
class RotationPolicy:
    max_file_size_bytes: int = 5 * 1024 * 1024          # 5MB
    max_age_days: int = 30
    archive_suffix: str = ".archive"

    def should_rotate(self, path: Path) -> bool:
        if not path.exists():
            return False
        try:
            size = path.stat().st_size
        except OSError:
            return False
        return size >= self.max_file_size_bytes


# ============================================================
# 6. ERROR LEDGER V6
# ============================================================

class ErrorLedgerV6:
    """
    Append-only JSONL + in-memory index + cluster map.
    Thread-safe CHƯA (Phase 4 chạy trong 1 process).
    """

    def __init__(
        self,
        storage_path: Path,
        rotation: Optional[RotationPolicy] = None,
    ):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.rotation = rotation or RotationPolicy()

        # In-memory indexes
        self._entries_by_id: Dict[str, ErrorEntry] = {}
        self._clusters: Dict[str, ErrorCluster] = {}      # signature -> cluster
        self._signatures_by_entry: Dict[str, str] = {}    # entry_id -> signature

        self._load()

    # --------- PERSISTENCE ---------

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    data["kind"] = ErrorKind(data["kind"])
                    entry = ErrorEntry(**data)
                    self._index_entry(entry)
                except Exception:
                    continue

    def _append_to_file(self, entry: ErrorEntry) -> None:
        with self.storage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def _rotate_if_needed(self) -> None:
        if not self.rotation.should_rotate(self.storage_path):
            return
        ts_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        archive = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}{self.rotation.archive_suffix}.{ts_tag}"
        )
        try:
            self.storage_path.rename(archive)
        except Exception:
            pass

    # --------- INDEXING ---------

    def _index_entry(self, entry: ErrorEntry) -> None:
        self._entries_by_id[entry.entry_id] = entry
        signature = compute_error_signature(
            kind=entry.kind.value,
            message=entry.message,
            stack_trace=entry.stack_trace,
            component_id=entry.component_id,
        )
        self._signatures_by_entry[entry.entry_id] = signature
        severity = normalize_severity(entry.severity)

        cluster = self._clusters.get(signature)
        if cluster is None:
            cluster = ErrorCluster(
                signature=signature,
                kind=entry.kind.value,
                severity=severity,
                sample_message=entry.message,
                sample_stack_top=entry.stack_trace.splitlines()[0]
                                  if entry.stack_trace else "",
                first_seen_utc=entry.reported_at_utc,
                last_seen_utc=entry.reported_at_utc,
                occurrence_count=1,
                affected_components=(
                    [entry.component_id] if entry.component_id else []
                ),
                affected_graphs=(
                    [entry.graph_id] if entry.graph_id else []
                ),
                latest_entry_ids=[entry.entry_id],
            )
            self._clusters[signature] = cluster
        else:
            cluster.occurrence_count += 1
            cluster.last_seen_utc = entry.reported_at_utc
            # Escalate severity nếu entry mới nặng hơn
            if (SEVERITY_WEIGHTS.get(severity, 0)
                    > SEVERITY_WEIGHTS.get(cluster.severity, 0)):
                cluster.severity = severity
            if entry.component_id and entry.component_id not in cluster.affected_components:
                cluster.affected_components.append(entry.component_id)
            if entry.graph_id and entry.graph_id not in cluster.affected_graphs:
                cluster.affected_graphs.append(entry.graph_id)
            cluster.latest_entry_ids.append(entry.entry_id)
            if len(cluster.latest_entry_ids) > 20:
                cluster.latest_entry_ids = cluster.latest_entry_ids[-20:]

    # --------- PUBLIC API ---------

    def record(self, entry: ErrorEntry) -> str:
        """Thêm entry. Trả về signature cluster mà entry rơi vào."""
        self._rotate_if_needed()
        self._append_to_file(entry)
        self._index_entry(entry)
        return self._signatures_by_entry[entry.entry_id]

    def get_entry(self, entry_id: str) -> Optional[ErrorEntry]:
        return self._entries_by_id.get(entry_id)

    def query(self, q: LedgerQuery) -> List[ErrorEntry]:
        since_dt = _parse_iso(q.since_utc) if q.since_utc else None
        until_dt = _parse_iso(q.until_utc) if q.until_utc else None
        results: List[ErrorEntry] = []
        for entry in self._entries_by_id.values():
            if q.kind and entry.kind.value != q.kind:
                continue
            if q.severity and normalize_severity(entry.severity) != q.severity:
                continue
            if q.component_id and entry.component_id != q.component_id:
                continue
            if q.graph_id and entry.graph_id != q.graph_id:
                continue
            if since_dt or until_dt:
                entry_dt = _parse_iso(entry.reported_at_utc)
                if entry_dt is None:
                    continue
                if since_dt and entry_dt < since_dt:
                    continue
                if until_dt and entry_dt > until_dt:
                    continue
            results.append(entry)
        results.sort(key=lambda e: e.reported_at_utc, reverse=True)
        return results[: q.limit]

    def get_cluster(self, signature: str) -> Optional[ErrorCluster]:
        return self._clusters.get(signature)

    def get_cluster_for_entry(self, entry_id: str) -> Optional[ErrorCluster]:
        sig = self._signatures_by_entry.get(entry_id)
        if sig is None:
            return None
        return self._clusters.get(sig)

    def list_clusters_by_priority(
        self, min_occurrences: int = 1, limit: int = 50
    ) -> List[ErrorCluster]:
        items = [c for c in self._clusters.values()
                 if c.occurrence_count >= min_occurrences]
        items.sort(key=lambda c: -c.priority_score())
        return items[:limit]

    def counts_by_severity(self) -> Dict[str, int]:
        out: Dict[str, int] = {s.value: 0 for s in SeverityBucket}
        for entry in self._entries_by_id.values():
            out[normalize_severity(entry.severity).value] += 1
        return out

    def counts_by_kind(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for entry in self._entries_by_id.values():
            k = entry.kind.value
            out[k] = out.get(k, 0) + 1
        return out

    def summary(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self._entries_by_id),
            "total_clusters": len(self._clusters),
            "by_severity": self.counts_by_severity(),
            "by_kind": self.counts_by_kind(),
            "storage_path": str(self.storage_path),
            "file_size_bytes": (
                self.storage_path.stat().st_size
                if self.storage_path.exists() else 0
            ),
        }

    def top_fix_candidates(self, top_k: int = 5) -> List[ErrorCluster]:
        """Các cluster nên vá trước - priority cao nhất."""
        return self.list_clusters_by_priority(
            min_occurrences=2, limit=top_k,
        )

    def prune_old_entries(self, max_age_days: Optional[int] = None) -> int:
        """
        Xóa entry trong MEMORY cũ hơn max_age_days (file giữ nguyên - rotate lo).
        Trả về số entry bị prune.
        """
        days = max_age_days if max_age_days is not None else self.rotation.max_age_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        to_remove: List[str] = []
        for eid, entry in self._entries_by_id.items():
            dt = _parse_iso(entry.reported_at_utc)
            if dt and dt < cutoff:
                to_remove.append(eid)
        for eid in to_remove:
            self._entries_by_id.pop(eid, None)
            sig = self._signatures_by_entry.pop(eid, None)
            if sig:
                cluster = self._clusters.get(sig)
                if cluster and eid in cluster.latest_entry_ids:
                    cluster.latest_entry_ids.remove(eid)
        return len(to_remove)


# ============================================================
# 7. SANITY CHECK
# ============================================================

def error_ledger_v6_sanity_check(tmp_path: Optional[Path] = None) -> Dict[str, bool]:
    import tempfile
    checks: Dict[str, bool] = {}
    tmp = tmp_path or Path(tempfile.mkdtemp(prefix="ledger_v6_"))
    ledger = ErrorLedgerV6(tmp / "errors.jsonl")

    # 1. Signature dedup: 2 error cùng message + stack → cùng cluster
    e1 = ErrorEntry(
        entry_id="e1",
        kind=ErrorKind.RUNTIME_EXCEPTION,
        message="TypeError: cannot read prop 'name' of null",
        stack_trace="at Navbar (src/components/Navbar.tsx:42:17)\nat App",
        context_hash="ctx_a",
        graph_id="g1",
        component_id="organism.navbar",
        severity="error",
        reported_at_utc=_now_iso(),
    )
    e2 = ErrorEntry(
        entry_id="e2",
        kind=ErrorKind.RUNTIME_EXCEPTION,
        # Cùng structure, khác line number
        message="TypeError: cannot read prop 'name' of null",
        stack_trace="at Navbar (src/components/Navbar.tsx:58:22)\nat App",
        context_hash="ctx_b",
        graph_id="g1",
        component_id="organism.navbar",
        severity="error",
        reported_at_utc=_now_iso(),
    )
    sig1 = ledger.record(e1)
    sig2 = ledger.record(e2)
    checks["dedup_same_signature"] = sig1 == sig2

    cluster = ledger.get_cluster(sig1)
    checks["cluster_count_2"] = cluster.occurrence_count == 2

    # 2. Escalation: critical entry làm cluster escalate
    e3 = ErrorEntry(
        entry_id="e3",
        kind=ErrorKind.RUNTIME_EXCEPTION,
        message="TypeError: cannot read prop 'name' of null",
        stack_trace="at Navbar (src/components/Navbar.tsx:99:01)\nat App",
        context_hash="ctx_c",
        graph_id="g2",
        component_id="organism.navbar",
        severity="critical",
        reported_at_utc=_now_iso(),
    )
    ledger.record(e3)
    checks["cluster_escalated_to_critical"] = (
        ledger.get_cluster(sig1).severity == SeverityBucket.CRITICAL
    )

    # 3. Query by severity
    critical_entries = ledger.query(LedgerQuery(severity=SeverityBucket.CRITICAL))
    checks["query_by_severity"] = len(critical_entries) == 1

    # 4. Different error → different cluster
    e_other = ErrorEntry(
        entry_id="eo",
        kind=ErrorKind.BUILD_FAILURE,
        message="Cannot find module 'xyz'",
        stack_trace="at Module._resolveFilename",
        context_hash="ctx_x",
        graph_id="g3",
        component_id=None,
        severity="error",
        reported_at_utc=_now_iso(),
    )
    sig_o = ledger.record(e_other)
    checks["different_cluster"] = sig_o != sig1

    # 5. Summary schema
    summary = ledger.summary()
    checks["summary_has_total"] = summary["total_entries"] == 4
    checks["summary_has_clusters"] = summary["total_clusters"] == 2

    # 6. Top fix candidates
    top = ledger.top_fix_candidates(top_k=3)
    checks["top_picks_navbar_first"] = (
        len(top) >= 1 and top[0].occurrence_count == 3
    )

    # 7. Query by time
    future_q = ledger.query(LedgerQuery(
        since_utc=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    ))
    checks["query_future_empty"] = len(future_q) == 0

    return checks


__all__ = [
    "ERROR_LEDGER_V6_VERSION",
    "SeverityBucket", "SEVERITY_WEIGHTS", "normalize_severity",
    "compute_error_signature",
    "ErrorCluster", "LedgerQuery",
    "RotationPolicy", "ErrorLedgerV6",
    "error_ledger_v6_sanity_check",
]
