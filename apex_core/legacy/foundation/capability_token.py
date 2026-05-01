"""
APEX Factory v5.0 Legacy - Capability Token System
Preserved from v5.0 for backward compatibility.

Implements NT5 (Human Supremacy) enforcement via capability-based access control.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Set

ALLOWED_SCOPES: FrozenSet[str] = frozenset({
    "read", "write", "deploy", "evolve", "admin",
    "build", "preview", "publish", "delete",
})


@dataclass
class CapabilityToken:
    """Token granting specific capabilities within the system."""
    token_id: str
    scopes: FrozenSet[str]
    issuer: str = "C2"
    issued_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    nonce: str = field(default_factory=lambda: hashlib.sha256(os.urandom(32)).hexdigest()[:16])

    def is_valid(self) -> bool:
        if self.expires_at and time.time() > self.expires_at:
            return False
        return all(s in ALLOWED_SCOPES for s in self.scopes)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "scopes": sorted(self.scopes),
            "issuer": self.issuer,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
        }


class CapabilityGate:
    """Gate that checks tokens before allowing operations."""

    def __init__(self, signer_or_scopes=None, nonce_store: Optional["NonceStore"] = None, required_scopes: Optional[Set[str]] = None):
        self._required_scopes: Set[str] = set()
        self._kill_switch_active: bool = False
        self._signer: Optional["CapabilityTokenSigner"] = None
        self._nonce_store: Optional["NonceStore"] = nonce_store

        if isinstance(signer_or_scopes, set):
            self._required_scopes = signer_or_scopes
        elif isinstance(signer_or_scopes, CapabilityTokenSigner):
            self._signer = signer_or_scopes
        elif required_scopes:
            self._required_scopes = required_scopes

    def check(self, token: Optional[CapabilityToken]) -> bool:
        if self._kill_switch_active:
            return False
        if token is None:
            return False
        if not token.is_valid():
            return False
        return all(token.has_scope(s) for s in self._required_scopes)

    def activate_kill_switch(self) -> None:
        self._kill_switch_active = True

    def deactivate_kill_switch(self) -> None:
        self._kill_switch_active = False


class KillSwitch:
    """Emergency kill switch - immediately halts all operations."""

    def __init__(self, state_path: Optional[Path] = None):
        self._active: bool = False
        self._reason: str = ""
        self._state_path = state_path
        if state_path and Path(state_path).exists():
            try:
                data = json.loads(Path(state_path).read_text())
                self._active = data.get("active", False)
                self._reason = data.get("reason", "")
            except (json.JSONDecodeError, OSError):
                pass

    @property
    def is_active(self) -> bool:
        return self._active

    def is_activated(self) -> bool:
        return self._active

    def activate(self, reason: str = "Emergency stop") -> None:
        self._active = True
        self._reason = reason

    def deactivate(self, master_secret: str) -> bool:
        expected = os.environ.get("C2_MASTER_SECRET", "")
        if expected and master_secret == expected:
            self._active = False
            self._reason = ""
            return True
        return False


class CapabilityTokenSigner:
    """Signs and verifies capability tokens."""

    def __init__(self, secret: Optional[str] = None):
        self._secret = secret or os.environ.get("C2_MASTER_SECRET", "dev-secret")

    def sign(self, token: CapabilityToken) -> str:
        payload = json.dumps(token.to_dict(), sort_keys=True)
        signature = hashlib.sha256(
            f"{payload}:{self._secret}".encode()
        ).hexdigest()
        return signature

    def verify(self, token: CapabilityToken, signature: str) -> bool:
        expected = self.sign(token)
        return signature == expected

    def issue_token(self, scopes: Set[str], ttl_seconds: int = 3600) -> CapabilityToken:
        token = CapabilityToken(
            token_id=hashlib.sha256(os.urandom(16)).hexdigest()[:12],
            scopes=frozenset(scopes & ALLOWED_SCOPES),
            expires_at=time.time() + ttl_seconds,
        )
        return token


class NonceStore:
    """Prevents token replay attacks via nonce tracking."""

    def __init__(self, store_path: Optional[Path] = None):
        self._store_path = store_path
        self._used_nonces: Set[str] = set()
        if store_path and store_path.exists():
            self._used_nonces = set(json.loads(store_path.read_text()))

    def check_and_consume(self, nonce: str) -> bool:
        if nonce in self._used_nonces:
            return False
        self._used_nonces.add(nonce)
        self._persist()
        return True

    def _persist(self) -> None:
        if self._store_path:
            self._store_path.write_text(json.dumps(sorted(self._used_nonces)))


__all__ = [
    "ALLOWED_SCOPES",
    "CapabilityToken",
    "CapabilityGate",
    "KillSwitch",
    "CapabilityTokenSigner",
    "NonceStore",
]
