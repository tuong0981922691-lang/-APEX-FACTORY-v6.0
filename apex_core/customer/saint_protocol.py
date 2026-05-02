"""Saint Protocol — customer UI rules (NT23 'Khách là Thánh').

Rules:
  - Font >= 18px
  - Contrast WCAG AAA
  - No ads, no popups, no covert tracking
  - Every AI question ends with "Anh xác nhận chứ?" / "Em hiểu đúng ý anh không?"
  - Has "Chốt rồi đừng hỏi nữa" skip button
"""

SAINT_CSS_PATH = "/site/static/css/saint.css"

SAINT_UI_RULES = {
    "min_font_size_px": 18,
    "contrast_ratio_min": 7.0,
    "no_ads": True,
    "no_popups": True,
    "no_tracking": True,
    "confirmation_suffixes": [
        "Anh xác nhận chứ?",
        "Em hiểu đúng ý anh không?",
        "Anh muốn thay đổi gì không?",
    ],
    "skip_button_text": "Chốt rồi đừng hỏi nữa",
}


def validate_ai_response(response: str) -> bool:
    """Check AI response ends with a confirmation question."""
    return any(response.rstrip().endswith(suffix) for suffix in SAINT_UI_RULES["confirmation_suffixes"])


def add_confirmation_suffix(response: str) -> str:
    """Add confirmation suffix if missing."""
    if validate_ai_response(response):
        return response
    return f"{response} Em hiểu đúng ý anh không?"
