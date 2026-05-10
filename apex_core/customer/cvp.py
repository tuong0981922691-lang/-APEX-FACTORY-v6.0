"""Customer Verification Protocol — 5 mechanisms (NT24).

Mechanisms:
  1. Live preview — customer sees demo at /preview/<order_id>
  2. Citation — each code block links to spec_freeze field
  3. Audit log visible — /customer/audit/<order_id> with masked PII
  4. Propose-confirm — each change requires customer OK before deploy
  5. Signed receipt — customer signs HMAC when accepting
"""
import hashlib
import hmac
import os
from datetime import datetime, timezone

from pydantic import BaseModel


class VerificationResult(BaseModel):
    mechanism: str
    passed: bool
    details: str
    timestamp: str


def live_preview_url(order_id: str) -> str:
    """Generate live preview URL for customer."""
    return f"/preview/{order_id}"


def citation_check(code_block: str, spec_fields: list[str]) -> VerificationResult:
    """Verify code block has citation to spec_freeze fields."""
    has_citation = any(field in code_block for field in spec_fields)
    return VerificationResult(
        mechanism="citation",
        passed=has_citation,
        details=f"Checked against {len(spec_fields)} spec fields",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def masked_audit_log(order_id: str, entries: list[dict]) -> list[dict]:
    """Return audit entries with PII masked for customer view."""
    masked = []
    for entry in entries:
        masked_entry = entry.copy()
        if "email" in masked_entry:
            email = masked_entry["email"]
            parts = email.split("@")
            masked_entry["email"] = f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else "***"
        if "phone" in masked_entry:
            masked_entry["phone"] = masked_entry["phone"][:4] + "***"
        masked.append(masked_entry)
    return masked


def propose_confirm(order_id: str, change_description: str) -> dict:
    """Create a propose-confirm request for customer."""
    return {
        "order_id": order_id,
        "change": change_description,
        "status": "pending_customer_confirm",
        "proposed_at": datetime.now(timezone.utc).isoformat(),
    }


def sign_receipt(order_id: str, customer_email: str, spec_hash: str) -> dict:
    """Generate signed receipt for customer acceptance."""
    secret = os.getenv("AUDIT_HMAC_SECRET", "default-dev-secret")
    payload = f"{order_id}:{customer_email}:{spec_hash}"
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {
        "order_id": order_id,
        "customer": customer_email,
        "spec_hash": spec_hash,
        "signature": signature,
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }
