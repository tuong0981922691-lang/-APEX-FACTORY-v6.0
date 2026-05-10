"""User store — JSON file-based storage (existing pattern)."""
import hashlib
import json
import secrets
from pathlib import Path
from typing import Optional


class UserStore:
    def __init__(self, storage_root: Optional[Path] = None):
        if storage_root is None:
            storage_root = Path(__file__).parent.parent.parent / "storage"
        self._dir = storage_root / "auth" / "users"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
        return f"{salt}:{hashed}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        salt, hashed = stored_hash.split(":", 1)
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest() == hashed

    def create(self, email: str, password: str, name: str = "") -> dict:
        user_id = secrets.token_urlsafe(12)
        user = {
            "id": user_id,
            "email": email,
            "password_hash": self._hash_password(password),
            "name": name,
        }
        path = self._dir / f"{user_id}.json"
        path.write_text(json.dumps(user))
        return {"id": user_id, "email": email, "name": name}

    def get_by_email(self, email: str) -> Optional[dict]:
        for f in self._dir.glob("*.json"):
            user = json.loads(f.read_text())
            if user.get("email") == email:
                return user
        return None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        path = self._dir / f"{user_id}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def verify(self, email: str, password: str) -> Optional[dict]:
        user = self.get_by_email(email)
        if not user:
            return None
        if self._verify_password(password, user["password_hash"]):
            return {"id": user["id"], "email": user["email"], "name": user.get("name", "")}
        return None
