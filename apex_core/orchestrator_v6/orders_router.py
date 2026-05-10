"""Orders router — customer order flow + CDP dialogue."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from apex_core.db.botthongminh_schema import get_db

router = APIRouter(prefix="/api/orders", tags=["orders"])


class OrderCreate(BaseModel):
    customer_email: str
    customer_phone: Optional[str] = None
    product_type: str
    spec_json: str
    amount_vnd: Optional[int] = None
    payment_method: Optional[str] = None


@router.post("/create")
def create_order(req: OrderCreate):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """INSERT INTO orders
        (customer_email, customer_phone, product_type, spec_json, status, created_at, amount_vnd, payment_method)
        VALUES (?, ?, ?, ?, 'pending_approval', ?, ?, ?)""",
        (req.customer_email, req.customer_phone, req.product_type, req.spec_json, now, req.amount_vnd, req.payment_method),
    )
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return {"ok": True, "order_id": order_id, "status": "pending_approval"}


@router.get("/list")
def list_orders(customer_email: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    if customer_email:
        cursor.execute("SELECT * FROM orders WHERE customer_email = ? ORDER BY id DESC", (customer_email,))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    orders = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return {"orders": orders, "count": len(orders)}


class CdpMessage(BaseModel):
    product_type: str
    message: str
    conversation_history: list[dict] = []


@router.post("/cdp")
def cdp_dialogue(req: CdpMessage):
    """CDP dialogue — LLM asks customer detailed questions about their requirements."""
    responses = {
        "website": "Bạn muốn website có bao nhiêu trang? Có cần tích hợp thanh toán không?",
        "mobile": "Ứng dụng cho iOS, Android hay cả hai? Có cần đăng nhập người dùng không?",
        "algorithm": "Thuật toán cần xử lý loại dữ liệu gì? Yêu cầu về tốc độ như thế nào?",
    }
    response_text = responses.get(
        req.product_type,
        "Hãy mô tả chi tiết hơn về yêu cầu của bạn."
    )
    return {
        "response": response_text,
        "turn": len(req.conversation_history) + 1,
        "complete": len(req.conversation_history) >= 2,
    }
