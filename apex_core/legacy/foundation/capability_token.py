"""Capability token and kill-switch primitives for local development."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Set

ALLOWED_SCOPES = frozenset({"deploy", "hot_inject", "kill_switch", "token"})


@dataclass(frozen=True)
class CapabilityToken:
    scope: str
    resource: str
    nonce: str
    signature: str


class KillSwitch:
    """File-backed kill switch."""

    def __init__(self, path: str | Path = "./apex_factory_storage/KILL_SWITCH") -> None:
        self.path = Path(path)

    def activate(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("activated
", encoding="utf-8")

    def deactivate(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def is_activated(self) -> bool:
        return self.path.exists()


class NonceStore:
    """In-memory nonce replay protection."""

    def __init__(self) -> None:
        self._seen: Set[str] = set()

    def remember(self, nonce: str) -> bool:
        if nonce in self._seen:
            return False
        self._seen.add(nonce)
        return True


class CapabilityTokenSigner:
    """Signs local capability tokens with HMAC-SHA256."""

    def __init__(self, master_secret: str | None = None) -> None:
        self.master_secret = master_secret or os.getenv("C2_MASTER_SECRET", "")

    @property
    def configured(self) -> bool:
        return bool(self.master_secret)

    def sign(self, scope: str, resource: str) -> CapabilityToken:
        if scope not in ALLOWED_SCOPES:
            raise ValueError(f"Unsupported capability scope: {scope}")
        if not self.master_secret:
            raise RuntimeError("C2_MASTER_SECRET is required to sign capability tokens")
        nonce = secrets.token_hex(16)
        payload = f"{scope}:{resource}:{nonce}".encode("utf-8")
        signature = hmac.new(self.master_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return CapabilityToken(scope=scope, resource=resource, nonce=nonce, signature=signature)


class CapabilityGate:
    """Validates tokens and prevents nonce replay."""

    def __init__(self, signer: CapabilityTokenSigner, nonce_store: NonceStore | None = None) -> None:
        self.signer = signer
        self.nonce_store = nonce_store or NonceStore()

    def verify(self, token: CapabilityToken) -> bool:
        if not self.signer.configured:
            return False
        payload = f"{token.scope}:{token.resource}:{token.nonce}".encode("utf-8")
        expected = hmac.new(self.signer.master_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, token.signature):
            return False
        return self.nonce_store.remember(token.nonce)


__all__ = [
    "ALLOWED_SCOPES",
    "CapabilityGate",
    "CapabilityToken",
    "CapabilityTokenSigner",
    "KillSwitch",
    "NonceStore",
]
