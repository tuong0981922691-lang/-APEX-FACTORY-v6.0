"""Notifications dispatcher — Telegram + Gmail."""
import logging
import os

logger = logging.getLogger(__name__)


async def send_telegram(message: str, chat_id: str | None = None) -> bool:
    """Send message via Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    target_chat_id = chat_id or os.getenv("TELEGRAM_OWNER_CHAT_ID")
    if not token or not target_chat_id:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_OWNER_CHAT_ID missing)")
        return False

    import httpx
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"chat_id": target_chat_id, "text": message, "parse_mode": "HTML"})
        return resp.status_code == 200


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP."""
    smtp_user = os.getenv("GMAIL_SMTP_USER")
    smtp_pass = os.getenv("GMAIL_SMTP_PASS")
    if not smtp_user or not smtp_pass:
        logger.warning("Gmail SMTP not configured")
        return False

    from email.mime.text import MIMEText

    import aiosmtplib

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to

    try:
        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=smtp_user,
            password=smtp_pass,
        )
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
