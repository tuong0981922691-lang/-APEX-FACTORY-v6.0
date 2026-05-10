"""2FA router — TOTP enrollment + verification."""
import os

import pyotp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/2fa", tags=["2fa"])

TOTP_ISSUER = os.getenv("TOTP_ISSUER", "BotThongMinh")


class EnrollResponse(BaseModel):
    secret: str
    provisioning_uri: str


class VerifyRequest(BaseModel):
    secret: str
    code: str


@router.post("/enroll")
def enroll_totp() -> EnrollResponse:
    """Generate a new TOTP secret for enrollment."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name="owner@botthongminh.com", issuer_name=TOTP_ISSUER)
    return EnrollResponse(secret=secret, provisioning_uri=uri)


@router.post("/verify")
def verify_totp(req: VerifyRequest):
    """Verify a TOTP code against a secret."""
    totp = pyotp.TOTP(req.secret)
    if totp.verify(req.code, valid_window=1):
        return {"ok": True, "verified": True}
    raise HTTPException(401, "Invalid TOTP code")
