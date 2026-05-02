"""SQLite schema for botthongminh.com v1 — 5 tables."""
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_email TEXT NOT NULL,
    customer_phone TEXT,
    product_type TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_approval',
    created_at TEXT NOT NULL,
    approved_at TEXT,
    approved_by TEXT,
    amount_vnd INTEGER,
    payment_method TEXT
);

CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_type TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_number TEXT NOT NULL,
    bank_name TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS notification_destinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,
    target TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS otp_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_hash TEXT NOT NULL,
    channel TEXT NOT NULL,
    purpose TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);

CREATE TABLE IF NOT EXISTS recovery_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL UNIQUE,
    channel_used TEXT NOT NULL,
    created_at TEXT NOT NULL,
    consumed_at TEXT
);
"""

_DB_PATH: Path | None = None


def _get_storage_root() -> Path:
    root = Path(__file__).parent.parent.parent / "storage"
    root.mkdir(parents=True, exist_ok=True)
    return root


def init_db(storage_root: Path | None = None) -> sqlite3.Connection:
    """Initialize database with schema, return connection."""
    if storage_root is None:
        storage_root = _get_storage_root()
    db_path = storage_root / "botthongminh.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def get_db() -> sqlite3.Connection:
    """Get a connection to the botthongminh database."""
    storage_root = _get_storage_root()
    db_path = storage_root / "botthongminh.db"
    if not db_path.exists():
        return init_db(storage_root)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
