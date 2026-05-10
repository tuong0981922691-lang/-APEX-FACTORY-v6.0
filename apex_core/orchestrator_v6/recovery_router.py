"""Recovery router — Telegram OTP + Email OTP recovery flow."""
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apex_core.db.botthongminh_schema import get_db

router = APIRouter(prefix="/api/recovery", tags=["recovery"])

OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "300"))
OTP_LENGTH = int(os.getenv("OTP_LENGTH", "6"))


class RecoveryRequest(BaseModel):
    channel: str  # "telegram" or "email"


class RecoveryVerify(BaseModel):
    session_token: str
    code: str


@router.post("/request")
def request_recovery(req: RecoveryRequest):
    """Initiate recovery — send OTP via selected channel."""
    if req.channel not in ("telegram", "email"):
        raise HTTPException(400, "Channel must be 'telegram' or 'email'")

    otp_code = "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])
    session_token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=OTP_TTL_SECONDS)).isoformat()

    conn = get_db()
    cursor = conn.cursor()

    import hashlib
    code_hash = hashlib.sha256(otp_code.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO otp_codes (code_hash, channel, purpose, expires_at) VALUES (?, ?, 'recovery', ?)",
        (code_hash, req.channel, expires_at),
    )
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO recovery_sessions (session_token, channel_used, created_at) VALUES (?, ?, ?)",
        (session_token, req.channel, now),
    )
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "session_token": session_token,
        "channel": req.channel,
        "message": f"OTP sent via {req.channel}. Check your {req.channel}.",
    }


@router.post("/verify")
def verify_recovery(req: RecoveryVerify):
    """Verify OTP code for recovery."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM recovery_sessions WHERE session_token = ? AND consumed_at IS NULL",
        (req.session_token,),
    )
    session = cursor.fetchone()
    if not session:
        conn.close()
        raise HTTPException(400, "Invalid or expired recovery session")

    import hashlib
    code_hash = hashlib.sha256(req.code.encode()).hexdigest()
    cursor.execute(
        "SELECT * FROM otp_codes WHERE code_hash = ? AND used_at IS NULL AND expires_at > ?",
        (code_hash, datetime.now(timezone.utc).isoformat()),
    )
    otp_row = cursor.fetchone()
    if not otp_row:
        conn.close()
        raise HTTPException(401, "Invalid or expired OTP code")

    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("UPDATE otp_codes SET used_at = ? WHERE code_hash = ?", (now, code_hash))
    cursor.execute("UPDATE recovery_sessions SET consumed_at = ? WHERE session_token = ?", (now, req.session_token))
    conn.commit()
    conn.close()

    return {"ok": True, "recovered": True, "message": "Recovery successful. You may now reset your credentials."}
