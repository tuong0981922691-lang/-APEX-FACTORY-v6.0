"""Tests for 2FA router."""
import pyotp
from apex_core.orchestrator_v6.studio_entry import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_enroll_totp():
    response = client.post("/api/2fa/enroll")
    assert response.status_code == 200
    data = response.json()
    assert "secret" in data
    assert "provisioning_uri" in data
    assert "otpauth://" in data["provisioning_uri"]


def test_verify_totp_valid():
    enroll = client.post("/api/2fa/enroll").json()
    secret = enroll["secret"]
    totp = pyotp.TOTP(secret)
    code = totp.now()
    response = client.post("/api/2fa/verify", json={"secret": secret, "code": code})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["verified"] is True


def test_verify_totp_invalid():
    enroll = client.post("/api/2fa/enroll").json()
    secret = enroll["secret"]
    response = client.post("/api/2fa/verify", json={"secret": secret, "code": "000000"})
    assert response.status_code == 401


def test_recovery_request():
    response = client.post("/api/recovery/request", json={"channel": "telegram"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "session_token" in data


def test_recovery_request_invalid_channel():
    response = client.post("/api/recovery/request", json={"channel": "sms"})
    assert response.status_code == 400
