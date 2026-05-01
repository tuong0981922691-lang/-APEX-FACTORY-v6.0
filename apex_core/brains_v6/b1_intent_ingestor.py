"""
APEX FACTORY v6.0 - Brains Layer (v6)
File: b1_intent_ingestor.py

Vai trò của B1: INTENT INGESTOR
    Input  : raw_text brief từ C2 (có thể đi qua PerceptionRouter trước
             nếu C2 đưa ảnh Figma / URL / voice)
    Output : BriefSpec (frozen, hashed) + domain + confidence

Không dùng LLM ở tầng parser chính (để offline-first hoạt động). Parser
dựa trên regex + keyword + domain heuristic. Nếu `context.llm_broker`
có sẵn, B1 gọi thêm bước "enrichment" để bổ sung features/tone tinh tế
hơn - nhưng mọi output LLM đều đi qua Schema Guard.

Thay thế B1Ingestor v5.0 (parser DSL xổ số).
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Mapping, Tuple

from apex_core.brains_v6.brain_base_v6 import (
    BrainStage,
    FactoryBrain,
    FactoryBrainContext,
    FactoryBrainResult,
)
from apex_core.foundation.domain_types import (
    heuristic_detect_domain,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)
from apex_core.legacy.foundation.contracts import now_utc_iso

# ============================================================
# 0. VERSION
# ============================================================

B1_VERSION = "6.0.0"


# ============================================================
# 1. BRIEF SPEC (immutable, hashed)
# ============================================================

@dataclass(frozen=True)
class BriefSpec:
    """
    Đặc tả brief sau khi B1 parse. Bất biến. SHA-256 hash để dùng làm
    brief_hash trong ProjectSnapshot.
    """
    brief_id: str
    raw_text: str                           # chuẩn hóa nhưng giữ nguyên ngữ
    domain: str                             # DomainType.value
    domain_confidence: float                # 0..1

    product_type: str                       # "landing_page" | "dashboard" | ...
    audience: str                           # mô tả ngắn
    tone: Tuple[str, ...]                   # ("minimal", "luxury", ...)
    color_preferences: Tuple[str, ...]      # ("deep blue", "warm beige")
    features: Tuple[str, ...]               # ("navbar", "pricing_table", ...)
    constraints: Mapping[str, Any]          # {"max_bundle_kb": 200, ...}
    references: Tuple[str, ...]             # URLs / file refs
    language: str = "vi"

    parse_confidence: float = 0.5
    parse_method: str = "regex"             # "regex" | "regex+llm" | "llm"
    extracted_at_utc: str = ""
    content_hash: str = ""

    def __post_init__(self):
        if not (0.0 <= self.domain_confidence <= 1.0):
            raise ValueError(f"domain_confidence out of [0,1]: {self.domain_confidence}")
        if not (0.0 <= self.parse_confidence <= 1.0):
            raise ValueError(f"parse_confidence out of [0,1]: {self.parse_confidence}")
        if not self.extracted_at_utc:
            object.__setattr__(self, "extracted_at_utc", now_utc_iso())
        if not self.content_hash:
            object.__setattr__(self, "content_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        payload = {
            "brief_id": self.brief_id,
            "raw_text": self.raw_text,
            "domain": self.domain,
            "product_type": self.product_type,
            "audience": self.audience,
            "tone": list(self.tone),
            "color_preferences": list(self.color_preferences),
            "features": list(self.features),
            "constraints": dict(self.constraints),
            "references": list(self.references),
            "language": self.language,
        }
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
            .encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "raw_text": self.raw_text,
            "domain": self.domain,
            "domain_confidence": self.domain_confidence,
            "product_type": self.product_type,
            "audience": self.audience,
            "tone": list(self.tone),
            "color_preferences": list(self.color_preferences),
            "features": list(self.features),
            "constraints": dict(self.constraints),
            "references": list(self.references),
            "language": self.language,
            "parse_confidence": self.parse_confidence,
            "parse_method": self.parse_method,
            "extracted_at_utc": self.extracted_at_utc,
            "content_hash": self.content_hash,
        }


# ============================================================
# 2. KEYWORD DICTIONARIES (Việt + Anh)
# ============================================================

PRODUCT_TYPE_KEYWORDS: Dict[str, FrozenSet[str]] = {
    "landing_page": frozenset({
        "landing", "landing page", "trang đích", "trang giới thiệu",
        "trang quảng cáo", "sales page",
    }),
    "dashboard": frozenset({
        "dashboard", "bảng điều khiển", "admin panel", "analytics",
        "thống kê", "quản trị",
    }),
    "ecommerce": frozenset({
        "ecommerce", "e-commerce", "shop", "cửa hàng", "bán hàng",
        "giỏ hàng", "checkout", "sản phẩm",
    }),
    "blog": frozenset({
        "blog", "bài viết", "cms", "news", "tin tức",
    }),
    "portfolio": frozenset({
        "portfolio", "cá nhân", "showcase", "trưng bày",
    }),
    "saas_app": frozenset({
        "saas", "b2b", "app web", "công cụ web", "productivity",
    }),
    "mobile_app": frozenset({
        "mobile app", "ứng dụng di động", "app điện thoại",
        "react native", "flutter app",
    }),
    "video_reel": frozenset({
        "reel", "short", "tiktok", "video ngắn",
    }),
    "image_banner": frozenset({
        "banner", "poster", "thumbnail", "ảnh bìa", "social card",
    }),
    "unknown": frozenset(),
}

TONE_KEYWORDS: Dict[str, FrozenSet[str]] = {
    "minimal": frozenset({"minimal", "tối giản", "sạch sẽ", "clean"}),
    "luxury": frozenset({"luxury", "sang trọng", "cao cấp", "premium", "elegant"}),
    "playful": frozenset({"playful", "vui nhộn", "fun", "cute", "dễ thương"}),
    "corporate": frozenset({"corporate", "chuyên nghiệp", "nghiêm túc", "serious"}),
    "tech": frozenset({"tech", "futuristic", "công nghệ", "khoa học viễn tưởng", "sci-fi"}),
    "warm": frozenset({"ấm áp", "gần gũi", "friendly", "warm"}),
    "bold": frozenset({"bold", "mạnh mẽ", "táo bạo", "ấn tượng"}),
    "editorial": frozenset({"editorial", "magazine", "tạp chí", "báo chí"}),
}

FEATURE_KEYWORDS: Dict[str, FrozenSet[str]] = {
    "navbar": frozenset({"navbar", "menu", "thanh điều hướng", "navigation"}),
    "hero": frozenset({"hero", "banner đầu", "cover", "bìa trang"}),
    "cta": frozenset({"cta", "call to action", "nút đăng ký", "nút mua", "nút kêu gọi"}),
    "pricing_table": frozenset({"pricing", "bảng giá", "gói dịch vụ"}),
    "testimonials": frozenset({"testimonial", "đánh giá khách hàng", "review", "feedback"}),
    "faq": frozenset({"faq", "câu hỏi thường gặp"}),
    "contact_form": frozenset({"contact form", "form liên hệ", "form đăng ký"}),
    "footer": frozenset({"footer", "chân trang"}),
    "auth": frozenset({"login", "sign up", "đăng ký", "đăng nhập", "auth"}),
    "search": frozenset({"search", "tìm kiếm"}),
    "dark_mode": frozenset({"dark mode", "chế độ tối", "theme tối"}),
    "multi_language": frozenset({"đa ngôn ngữ", "i18n", "multi-language"}),
    "blog_list": frozenset({"blog list", "danh sách bài viết", "article list"}),
    "product_grid": frozenset({"product grid", "lưới sản phẩm", "danh sách sản phẩm"}),
    "cart": frozenset({"cart", "giỏ hàng", "shopping cart"}),
    "checkout": frozenset({"checkout", "thanh toán"}),
    "animation": frozenset({"animation", "hiệu ứng", "motion", "chuyển động"}),
}

# Regex bắt số cụ thể cho constraints
RE_BUNDLE_KB = re.compile(r"(\d{2,4})\s*kb", re.IGNORECASE)
RE_MAX_LCP_SEC = re.compile(r"lcp\s*(?:dưới|under|<)?\s*(\d+(?:\.\d+)?)\s*s", re.IGNORECASE)
RE_WCAG = re.compile(r"wcag\s*(2\.[12])\s*(aa|aaa)", re.IGNORECASE)

# Regex URL
RE_URL = re.compile(r"https?://[^\s,]+", re.IGNORECASE)


# ============================================================
# 3. TEXT NORMALIZER (Vietnamese-aware)
# ============================================================

class BriefNormalizer:
    WS_RE = re.compile(r"\s+")
    CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFC", text)
        text = BriefNormalizer.CTRL_RE.sub("", text)
        text = BriefNormalizer.WS_RE.sub(" ", text).strip()
        return text

    @staticmethod
    def detect_language(text: str) -> str:
        """Rất đơn giản: nếu có dấu tiếng Việt → vi, ngược lại → en."""
        viet_pattern = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.IGNORECASE)
        return "vi" if viet_pattern.search(text) else "en"


# ============================================================
# 4. PARSER STAGES (có thể hot-plug)
# ============================================================

@dataclass(frozen=True)
class ParseOutput:
    product_type: str
    audience: str
    tone: Tuple[str, ...]
    color_preferences: Tuple[str, ...]
    features: Tuple[str, ...]
    constraints: Dict[str, Any]
    references: Tuple[str, ...]
    confidence: float
    method: str


class RegexKeywordParser:
    """
    Parser chính - offline, không cần LLM. Nhanh, tin cậy ~60-75%.
    """

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def parse(self, text: str, language: str) -> ParseOutput:
        lower = text.lower()

        product_type = self._detect_product_type(lower)
        tone = self._detect_tone(lower)
        features = self._detect_features(lower)
        colors = self._detect_colors(lower, language)
        references = self._extract_references(text)
        constraints = self._extract_constraints(text, lower)
        audience = self._extract_audience(text, language)

        # Confidence: tổng hợp coverage của các field
        signals = 0
        signals += 1 if product_type != "unknown" else 0
        signals += 1 if tone else 0
        signals += 1 if features else 0
        signals += 1 if colors else 0
        signals += 1 if references else 0
        signals += 1 if constraints else 0
        signals += 1 if audience else 0

        # Tối đa 7 signal → scale về [0.25, 0.85]
        confidence = round(0.25 + (signals / 7.0) * 0.6, 3)

        return ParseOutput(
            product_type=product_type,
            audience=audience,
            tone=tone,
            color_preferences=colors,
            features=features,
            constraints=constraints,
            references=references,
            confidence=confidence,
            method="regex",
        )

    def _detect_product_type(self, lower: str) -> str:
        scores: Dict[str, int] = {}
        for ptype, keywords in PRODUCT_TYPE_KEYWORDS.items():
            if ptype == "unknown":
                continue
            count = sum(1 for kw in keywords if kw in lower)
            if count > 0:
                scores[ptype] = count
        if not scores:
            return "unknown"
        return max(scores.items(), key=lambda kv: kv[1])[0]

    def _detect_tone(self, lower: str) -> Tuple[str, ...]:
        detected: List[str] = []
        for tone, keywords in TONE_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                detected.append(tone)
        return tuple(detected)

    def _detect_features(self, lower: str) -> Tuple[str, ...]:
        detected: List[str] = []
        for feature, keywords in FEATURE_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                detected.append(feature)
        return tuple(detected)

    def _detect_colors(self, lower: str, language: str) -> Tuple[str, ...]:
        """Bắt color preference thô. Không resolve thành hex ở đây."""
        vi_colors = {
            "xanh dương", "xanh lá", "xanh biển", "xanh navy", "đỏ", "vàng",
            "cam", "tím", "hồng", "đen", "trắng", "xám", "be",
            "nâu", "pastel", "gradient",
        }
        en_colors = {
            "blue", "red", "green", "yellow", "orange", "purple",
            "pink", "black", "white", "gray", "grey", "beige",
            "brown", "pastel", "gradient", "neon",
        }
        palette = vi_colors if language == "vi" else en_colors
        detected: List[str] = []
        for color in palette:
            if color in lower:
                detected.append(color)
        return tuple(detected)

    def _extract_references(self, text: str) -> Tuple[str, ...]:
        urls = RE_URL.findall(text)
        # Dedup và giữ thứ tự
        seen = set()
        unique: List[str] = []
        for u in urls:
            u = u.rstrip(",.")
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return tuple(unique)

    def _extract_constraints(self, text: str, lower: str) -> Dict[str, Any]:
        constraints: Dict[str, Any] = {}

        m = RE_BUNDLE_KB.search(lower)
        if m:
            try:
                constraints["max_bundle_kb"] = int(m.group(1))
            except ValueError:
                pass

        m = RE_MAX_LCP_SEC.search(lower)
        if m:
            try:
                constraints["max_lcp_seconds"] = float(m.group(1))
            except ValueError:
                pass

        m = RE_WCAG.search(text)
        if m:
            constraints["wcag_version"] = m.group(1)
            constraints["wcag_level"] = m.group(2).upper()

        if "ssr" in lower or "server side render" in lower:
            constraints["rendering"] = "ssr"
        elif "spa" in lower or "client side" in lower:
            constraints["rendering"] = "csr"

        if "responsive" in lower or "đa thiết bị" in lower:
            constraints["responsive_required"] = True

        if "dark mode" in lower or "chế độ tối" in lower:
            constraints["dark_mode_required"] = True

        return constraints

    def _extract_audience(self, text: str, language: str) -> str:
        """
        Heuristic: tìm câu chứa 'audience', 'khách hàng', 'người dùng', 'dành cho'...
        Trả chuỗi ngắn.
        """
        patterns = (
            r"(?:dành cho|target|audience|for)\s+([^.!?\n]+)",
            r"(?:khách hàng|người dùng|users?)\s+(?:là|are)\s+([^.!?\n]+)",
        )
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                audience = m.group(1).strip()
                return audience[:200]
        return ""


# ============================================================
# 5. LLM ENRICHER (optional, đi qua Schema Guard - Phase 5 chi tiết)
# ============================================================

class LLMEnricher:
    """
    Khi context.llm_broker có sẵn, gọi LLM để bổ sung:
      - tone tinh tế (từ "premium" suy ra "editorial + warm")
      - audience chi tiết (từ "dành cho founder startup" suy ra persona)

    Schema output BẮT BUỘC. Nếu không khớp → bỏ, dùng output regex.
    Phase 5 (llm_broker.py + schema_guard.py) implement đầy đủ.
    """
    EXPECTED_KEYS = frozenset({
        "tone_refined", "audience_refined", "features_suggested",
    })

    def enrich(
        self,
        base: ParseOutput,
        raw_text: str,
        llm_broker: Any,
    ) -> Tuple[ParseOutput, int]:
        """Return (refined_parse, llm_call_count)."""
        if llm_broker is None:
            return base, 0

        # Placeholder: ở Phase 5 gọi llm_broker.call(prompt, schema).
        # Hiện tại trả base không đổi + 0 calls.
        # KHI có broker thật, đoạn dưới sẽ enable.
        try:
            schema = {
                "type": "object",
                "required": ["tone_refined", "audience_refined", "features_suggested"],
                "properties": {
                    "tone_refined":         {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                    "audience_refined":     {"type": "string", "maxLength": 300},
                    "features_suggested":   {"type": "array", "items": {"type": "string"}, "maxItems": 10},
                },
                "additionalProperties": False,
            }
            prompt = (
                "Extract refined tone, audience, and suggested features from this brief. "
                "Output MUST be valid JSON matching the schema. "
                f"\n\nBrief:\n{raw_text[:2000]}"
            )
            response = llm_broker.call_with_schema(
                prompt=prompt,
                schema=schema,
                temperature=0.2,
                max_retries=2,
            )
            if not isinstance(response, dict):
                return base, 1

            merged_tone = tuple(sorted(set(base.tone) | set(response.get("tone_refined", []))))
            merged_features = tuple(sorted(
                set(base.features) | set(response.get("features_suggested", []))
            ))
            refined_audience = response.get("audience_refined") or base.audience

            return ParseOutput(
                product_type=base.product_type,
                audience=refined_audience,
                tone=merged_tone,
                color_preferences=base.color_preferences,
                features=merged_features,
                constraints=base.constraints,
                references=base.references,
                confidence=min(0.92, base.confidence + 0.15),   # boost nhẹ
                method="regex+llm",
            ), 1
        except Exception:
            # Schema fail / broker fail → fallback base, KHÔNG crash B1
            return base, 1


# ============================================================
# 6. B1 INTENT INGESTOR BRAIN
# ============================================================

class B1IntentIngestor(FactoryBrain):
    """
    B1 - INTENT INGESTOR (v6.0 Factory).
    Input:  context.shared_memory["raw_brief"]
    Output: context.brief_spec + shared_memory["brief_dict"]
    """

    BRAIN_ID = "B1_v6"
    BRAIN_NAME = "IntentIngestor"
    BRAIN_STAGE = BrainStage.INGEST
    REQUIRED_INPUTS = ("raw_brief",)

    def __init__(self, hooks=None):
        super().__init__(hooks=hooks)
        self.normalizer = BriefNormalizer()
        self.regex_parser = RegexKeywordParser()
        self.enricher = LLMEnricher()

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def execute(self, context: FactoryBrainContext) -> FactoryBrainResult:
        raw = context.shared_memory.get("raw_brief")
        if not isinstance(raw, str) or not raw.strip():
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID,
                success=False,
                outputs={},
                errors=["raw_brief is empty or not string"],
                stage=self.BRAIN_STAGE.value,
            )

        # Step 1: Normalize
        normalized = self.normalizer.normalize(raw)
        if len(normalized) < 10:
            return FactoryBrainResult(
                brain_id=self.BRAIN_ID,
                success=False,
                outputs={},
                errors=[f"Brief quá ngắn ({len(normalized)} chars) để parse có ý nghĩa"],
                stage=self.BRAIN_STAGE.value,
            )
        language = self.normalizer.detect_language(normalized)

        # Step 2: Detect domain
        domain, domain_conf = heuristic_detect_domain(normalized)

        # Step 3: Regex parse
        regex_result = self.regex_parser.parse(normalized, language)

        # Step 4: Optional LLM enrichment (qua Schema Guard)
        llm_calls = 0
        final_parse = regex_result
        if context.has_llm():
            final_parse, llm_calls = self.enricher.enrich(
                regex_result, normalized, context.llm_broker,
            )

        # Step 5: Build BriefSpec
        brief = BriefSpec(
            brief_id=self._gen_brief_id(normalized),
            raw_text=normalized[:4000],
            domain=domain.value,
            domain_confidence=domain_conf,
            product_type=final_parse.product_type,
            audience=final_parse.audience,
            tone=final_parse.tone,
            color_preferences=final_parse.color_preferences,
            features=final_parse.features,
            constraints=dict(final_parse.constraints),
            references=final_parse.references,
            language=language,
            parse_confidence=final_parse.confidence,
            parse_method=final_parse.method,
        )

        # Step 6: Attach to context (shared state for next brains)
        context.brief_spec = brief
        context.target_domain = domain

        # Step 7: Build result
        warnings: List[str] = []
        if brief.parse_confidence < 0.4:
            warnings.append(
                f"Parse confidence thấp ({brief.parse_confidence:.2f}) - "
                f"C2 nên bổ sung brief"
            )
        if brief.product_type == "unknown":
            warnings.append("Không xác định được product_type - B2 sẽ quét rộng")
        if not brief.features:
            warnings.append("Không phát hiện feature nào - brief có thể quá mơ hồ")

        outputs: Dict[str, Any] = {
            "brief_dict": brief.to_dict(),
            "brief_id": brief.brief_id,
            "domain": brief.domain,
            "domain_confidence": brief.domain_confidence,
            "product_type": brief.product_type,
            "features_count": len(brief.features),
            "tones_count": len(brief.tone),
        }
        # Cho các brain sau đọc qua shared_memory
        context.shared_memory["brief_dict"] = brief.to_dict()
        context.shared_memory["brief_id"] = brief.brief_id

        return FactoryBrainResult(
            brain_id=self.BRAIN_ID,
            success=True,
            outputs=outputs,
            warnings=warnings,
            metrics={
                "parse_confidence": brief.parse_confidence,
                "domain_confidence": brief.domain_confidence,
                "features_extracted": float(len(brief.features)),
                "references_extracted": float(len(brief.references)),
                "text_length": float(len(brief.raw_text)),
            },
            stage=self.BRAIN_STAGE.value,
            llm_calls=llm_calls,
        )

    def _gen_brief_id(self, normalized: str) -> str:
        prefix = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return f"brief_{prefix}"


# ============================================================
# 7. SANITY CHECK
# ============================================================

def b1_intent_ingestor_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    brain = B1IntentIngestor()

    # Case 1: Brief web landing
    ctx = FactoryBrainContext(
        run_id="r1",
        current_date="2025-01-01",
        draws=[],
        current_idx=0,
        shared_memory={
            "raw_brief": (
                "Tôi cần landing page bán khóa học AI dành cho founder startup. "
                "Tone cao cấp và tối giản. Màu xanh navy chủ đạo. "
                "Cần navbar, hero, pricing, testimonials, footer. "
                "Bundle tối đa 250kb. WCAG 2.2 AA. Dark mode required. "
                "Tham khảo https://linear.app và https://stripe.com"
            ),
        },
    )
    result = brain.run(ctx)
    checks["run_success"] = result.success
    if result.success:
        brief = ctx.brief_spec
        checks["brief_attached"] = brief is not None
        checks["domain_is_web"] = brief.domain == "web"
        checks["product_type_landing"] = brief.product_type == "landing_page"
        checks["tone_detected"] = len(brief.tone) >= 1
        checks["features_detected"] = "navbar" in brief.features and "pricing_table" in brief.features
        checks["constraints_bundle"] = brief.constraints.get("max_bundle_kb") == 250
        checks["constraints_wcag"] = brief.constraints.get("wcag_level") == "AA"
        checks["references_count"] = len(brief.references) == 2
        checks["content_hash_nonempty"] = bool(brief.content_hash)
        checks["language_vi"] = brief.language == "vi"

    # Case 2: Brief video reel
    ctx2 = FactoryBrainContext(
        run_id="r2",
        current_date="2025-01-01",
        draws=[],
        current_idx=0,
        shared_memory={
            "raw_brief": "Make a 15-second TikTok reel about coffee, playful tone, warm colors",
        },
    )
    result2 = brain.run(ctx2)
    checks["video_run_success"] = result2.success
    if result2.success:
        checks["video_domain"] = ctx2.brief_spec.domain == "video"
        checks["video_language_en"] = ctx2.brief_spec.language == "en"
        checks["video_tone_playful"] = "playful" in ctx2.brief_spec.tone

    # Case 3: Empty brief
    ctx3 = FactoryBrainContext(
        run_id="r3",
        current_date="2025-01-01",
        draws=[],
        current_idx=0,
        shared_memory={"raw_brief": ""},
    )
    result3 = brain.run(ctx3)
    checks["empty_brief_fails"] = not result3.success

    # Case 4: Missing raw_brief key
    ctx4 = FactoryBrainContext(
        run_id="r4",
        current_date="2025-01-01",
        draws=[],
        current_idx=0,
        shared_memory={},
    )
    result4 = brain.run(ctx4)
    checks["missing_key_fails"] = not result4.success

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "B1_VERSION",
    "BriefSpec",
    "PRODUCT_TYPE_KEYWORDS",
    "TONE_KEYWORDS",
    "FEATURE_KEYWORDS",
    "BriefNormalizer",
    "ParseOutput",
    "RegexKeywordParser",
    "LLMEnricher",
    "B1IntentIngestor",
    "b1_intent_ingestor_sanity_check",
]
