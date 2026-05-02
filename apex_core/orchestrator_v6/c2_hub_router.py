"""C2 Hub router — 8 module M1-M8."""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apex_core.db.botthongminh_schema import get_db

router = APIRouter(prefix="/api/c2", tags=["c2-hub"])


@router.get("/health")
def c2_health():
    return {"ok": True, "module": "c2-hub", "modules": 8}


# M1: Ingest link
class IngestRequest(BaseModel):
    url: str
    link_type: str = "ai"


@router.post("/ingest")
def ingest_link(req: IngestRequest):
    return {"ok": True, "url": req.url, "type": req.link_type, "status": "queued"}


# M2: Mining queue
@router.get("/mining")
def mining_queue():
    return {"items": [], "count": 0}


# M3: Probe panel
@router.get("/probe")
def probe_panel():
    return {"probes": [], "last_run": None}


# M4: Audit stream
@router.get("/audit-stream")
def audit_stream():
    return {"entries": [], "total": 0}


# M5: Orders
@router.get("/orders")
def list_orders(status: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM orders WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    orders = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return {"orders": orders, "count": len(orders)}


@router.post("/orders/{order_id}/approve")
def approve_order(order_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        raise HTTPException(404, "Order not found")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "UPDATE orders SET status = 'approved', approved_at = ?, approved_by = 'c2' WHERE id = ?",
        (now, order_id),
    )
    conn.commit()
    conn.close()
    return {"ok": True, "order_id": order_id, "status": "approved"}


# M6: Wallets
@router.get("/wallets")
def list_wallets():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wallets ORDER BY id")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    wallets = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return {"wallets": wallets}


class WalletCreate(BaseModel):
    wallet_type: str
    account_name: str
    account_number: str
    bank_name: Optional[str] = None


@router.post("/wallets")
def create_wallet(req: WalletCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO wallets (wallet_type, account_name, account_number, bank_name) VALUES (?, ?, ?, ?)",
        (req.wallet_type, req.account_name, req.account_number, req.bank_name),
    )
    conn.commit()
    wallet_id = cursor.lastrowid
    conn.close()
    return {"ok": True, "id": wallet_id}


# M7: Notifications
@router.get("/notifications")
def list_notifications():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notification_destinations ORDER BY id")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    dests = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return {"destinations": dests}


class NotificationDestCreate(BaseModel):
    channel: str
    target: str


@router.post("/notifications")
def create_notification_dest(req: NotificationDestCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notification_destinations (channel, target) VALUES (?, ?)",
        (req.channel, req.target),
    )
    conn.commit()
    dest_id = cursor.lastrowid
    conn.close()
    return {"ok": True, "id": dest_id}


# M8: Security
@router.get("/security")
def security_info():
    return {"otp_channels": ["telegram", "email"], "recovery_available": True}
