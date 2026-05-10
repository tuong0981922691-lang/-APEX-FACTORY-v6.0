"""Customer Dialogue Protocol — 5-stage state machine (NT23/NT24).

Stages:
  1. Ingest — customer pastes initial idea
  2. Vision — AI asks "What do you want the app to do? How should it look?"
  3. Description — AI summarizes → "Is this correct?"
  4. Detail — AI asks deeper until schema is complete
  5. Spec Freeze — Owner C2 signs → spec_freeze.json + capability token
"""
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class CDPStage(str, Enum):
    INGEST = "ingest"
    VISION = "vision"
    DESCRIPTION = "description"
    DETAIL = "detail"
    SPEC_FREEZE = "spec_freeze"


class CDPSession(BaseModel):
    order_id: str
    stage: CDPStage = CDPStage.INGEST
    customer_email: str
    product_type: str
    conversation: list[dict] = []
    spec_draft: Optional[dict] = None
    spec_frozen: bool = False
    created_at: str = ""
    updated_at: str = ""


STAGE_QUESTIONS = {
    CDPStage.VISION: "Bạn muốn ứng dụng này làm gì? Trông ra sao? Em hiểu đúng ý anh không?",
    CDPStage.DESCRIPTION: "Em tóm tắt lại yêu cầu như sau: {summary}. Anh xác nhận chứ?",
    CDPStage.DETAIL: "Để em hiểu rõ hơn: {detail_question}. Anh xác nhận chứ?",
}


def create_session(order_id: str, customer_email: str, product_type: str) -> CDPSession:
    """Create a new CDP session."""
    now = datetime.now(timezone.utc).isoformat()
    return CDPSession(
        order_id=order_id,
        customer_email=customer_email,
        product_type=product_type,
        created_at=now,
        updated_at=now,
    )


def advance_stage(session: CDPSession, customer_message: str) -> tuple[CDPSession, str]:
    """Advance CDP to the next stage based on customer input."""
    session.conversation.append({"role": "customer", "content": customer_message})
    session.updated_at = datetime.now(timezone.utc).isoformat()

    if session.stage == CDPStage.INGEST:
        session.stage = CDPStage.VISION
        response = STAGE_QUESTIONS[CDPStage.VISION]
    elif session.stage == CDPStage.VISION:
        session.stage = CDPStage.DESCRIPTION
        response = STAGE_QUESTIONS[CDPStage.DESCRIPTION].format(summary=customer_message[:200])
    elif session.stage == CDPStage.DESCRIPTION:
        session.stage = CDPStage.DETAIL
        response = STAGE_QUESTIONS[CDPStage.DETAIL].format(detail_question="Có tính năng nào khác không?")
    elif session.stage == CDPStage.DETAIL:
        session.stage = CDPStage.SPEC_FREEZE
        session.spec_draft = {"description": customer_message, "product_type": session.product_type}
        response = "Spec đã sẵn sàng. Chờ Owner xác nhận để đóng băng yêu cầu."
    else:
        response = "Spec đã được đóng băng. Đơn hàng đang chờ xử lý."

    session.conversation.append({"role": "assistant", "content": response})
    return session, response


def freeze_spec(session: CDPSession, data_root: Path) -> Path:
    """Freeze the spec and write to disk."""
    order_dir = data_root / "orders" / session.order_id
    order_dir.mkdir(parents=True, exist_ok=True)
    spec_file = order_dir / "spec_freeze.json"
    spec_data = {
        "order_id": session.order_id,
        "product_type": session.product_type,
        "spec": session.spec_draft,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "conversation_turns": len(session.conversation),
    }
    spec_file.write_text(json.dumps(spec_data, indent=2, ensure_ascii=False))
    session.spec_frozen = True
    return spec_file
