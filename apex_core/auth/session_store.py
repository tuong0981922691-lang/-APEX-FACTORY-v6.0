"""Session store — JSON file-based storage (existing pattern)."""
import json
import time
from pathlib import Path
from typing import Optional


class SessionStore:
    def __init__(self, storage_root: Optional[Path] = None, ttl_seconds: int = 86400):
        if storage_root is None:
            storage_root = Path(__file__).parent.parent.parent / "storage"
        self._dir = storage_root / "auth" / "sessions"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl_seconds

    def create(self, token: str, user_id: str) -> dict:
        session = {
            "token": token,
            "user_id": user_id,
            "created_at": time.time(),
        }
        path = self._dir / f"{token[:16]}.json"
        path.write_text(json.dumps(session))
        return session

    def get(self, token: str) -> Optional[dict]:
        path = self._dir / f"{token[:16]}.json"
        if not path.exists():
            return None
        session = json.loads(path.read_text())
        if time.time() - session["created_at"] > self._ttl:
            path.unlink(missing_ok=True)
            return None
        return session

    def delete(self, token: str) -> None:
        path = self._dir / f"{token[:16]}.json"
        path.unlink(missing_ok=True)
