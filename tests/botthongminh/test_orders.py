"""Tests for Orders router."""
from apex_core.orchestrator_v6.studio_entry import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_order():
    response = client.post("/api/orders/create", json={
        "customer_email": "test@example.com",
        "product_type": "website",
        "spec_json": '{"description": "Landing page for my business"}',
        "amount_vnd": 5000000,
        "payment_method": "momo",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["status"] == "pending_approval"
    assert "order_id" in data


def test_list_orders():
    response = client.get("/api/orders/list")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert data["count"] >= 0


def test_cdp_dialogue():
    response = client.post("/api/orders/cdp", json={
        "product_type": "website",
        "message": "I want a landing page",
        "conversation_history": [],
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["turn"] == 1


def test_cdp_dialogue_complete():
    response = client.post("/api/orders/cdp", json={
        "product_type": "mobile",
        "message": "Yes that's fine",
        "conversation_history": [{"role": "user", "content": "I want an app"}, {"role": "assistant", "content": "What kind?"}],
    })
    assert response.status_code == 200
    data = response.json()
    assert data["complete"] is True
