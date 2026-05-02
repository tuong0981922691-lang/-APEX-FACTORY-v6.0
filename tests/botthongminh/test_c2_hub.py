"""Tests for C2 Hub router."""
from apex_core.orchestrator_v6.studio_entry import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_c2_health():
    response = client.get("/api/c2/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["module"] == "c2-hub"
    assert data["modules"] == 8


def test_ingest_link():
    response = client.post("/api/c2/ingest", json={"url": "https://example.com", "link_type": "ai"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["status"] == "queued"


def test_list_orders_empty():
    response = client.get("/api/c2/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "count" in data


def test_list_wallets():
    response = client.get("/api/c2/wallets")
    assert response.status_code == 200
    data = response.json()
    assert "wallets" in data


def test_create_wallet():
    response = client.post("/api/c2/wallets", json={
        "wallet_type": "momo",
        "account_name": "Test Account",
        "account_number": "0901234567",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "id" in data


def test_notifications_list():
    response = client.get("/api/c2/notifications")
    assert response.status_code == 200
    data = response.json()
    assert "destinations" in data


def test_security_info():
    response = client.get("/api/c2/security")
    assert response.status_code == 200
    data = response.json()
    assert "telegram" in data["otp_channels"]
