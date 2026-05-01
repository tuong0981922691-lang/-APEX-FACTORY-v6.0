"""
APEX FACTORY v6.0 - External Integration Layer
File: llm_broker.py

Mục đích: Broker đa nhà cung cấp LLM với common interface.
    Mọi output LLM bắt buộc đi qua SchemaGuard (file trên) TRƯỚC khi
    hệ thống dùng. Đó là "Giao thức Mượn Tổ" đầy đủ.

Adapters:
    - OpenAIAdapter     (GPT-4o, GPT-4 Turbo, GPT-3.5)
    - AnthropicAdapter  (Claude 3.5 Sonnet, Opus, Haiku)
    - GeminiAdapter     (Gemini 1.5 Pro, Flash)
    - OllamaAdapter     (local models: llama3, qwen, deepseek)
    - MockAdapter       (cho test)

Tính năng:
    - Graceful degradation khi SDK chưa install
    - Multi-provider fallback (primary fail → secondary → ...)
    - Cost tracking per call (prompt/completion tokens + $)
    - Response caching (prompt_hash → cached response)
    - Audit trail riêng vào llm_audit.jsonl
    - NT5 enforcement: Broker không tự emit; C2 phải gọi thông qua BorrowingProtocol
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from apex_core.external.schema_guard import (
    RetryHarness,
    RetryOutcome,
    RetryPolicy,
    SchemaGuard,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)

# ============================================================
# 0. VERSION
# ============================================================

LLM_BROKER_VERSION = "6.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# 1. PROVIDER ENUM + COST TABLE (USD per 1M tokens)
# ============================================================

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    MOCK = "mock"


# Giá ước tính USD/1M tokens tại thời điểm viết (C2 update khi giá đổi)
# Format: {model: (input_usd_per_1m, output_usd_per_1m)}
COST_TABLE: Dict[str, Tuple[float, float]] = {
    "gpt-4o":                 (2.50, 10.00),
    "gpt-4o-mini":            (0.15, 0.60),
    "gpt-4-turbo":            (10.00, 30.00),
    "gpt-3.5-turbo":          (0.50, 1.50),
    "claude-3-5-sonnet":      (3.00, 15.00),
    "claude-3-5-haiku":       (0.80, 4.00),
    "claude-3-opus":          (15.00, 75.00),
    "gemini-1.5-pro":         (1.25, 5.00),
    "gemini-1.5-flash":       (0.075, 0.30),
    "llama3:8b":              (0.0, 0.0),        # local
    "qwen2.5-coder:7b":       (0.0, 0.0),        # local
    "mock":                   (0.0, 0.0),
}


def estimate_cost_usd(
    model: str, prompt_tokens: int, completion_tokens: int,
) -> float:
    in_rate, out_rate = COST_TABLE.get(model, (0.0, 0.0))
    return (
        (prompt_tokens / 1_000_000) * in_rate
        + (completion_tokens / 1_000_000) * out_rate
    )


# ============================================================
# 2. REQUEST / RESPONSE TYPES
# ============================================================

@dataclass
class LLMRequest:
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 2048
    model: Optional[str] = None        # None → adapter default
    json_mode: bool = False
    stop: Optional[List[str]] = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    provider: LLMProvider
    model: str
    raw_text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    elapsed_ms: float = 0.0
    finish_reason: str = "stop"
    error: Optional[str] = None
    cached: bool = False

    def ok(self) -> bool:
        return self.error is None and bool(self.raw_text)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model": self.model,
            "raw_text_len": len(self.raw_text),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "elapsed_ms": round(self.elapsed_ms, 2),
            "finish_reason": self.finish_reason,
            "error": self.error,
            "cached": self.cached,
        }


# ============================================================
# 3. ADAPTER BASE + IMPLEMENTATIONS
# ============================================================

class LLMAdapter:
    PROVIDER: LLMProvider = LLMProvider.MOCK
    DEFAULT_MODEL: str = "mock"

    def is_available(self) -> bool:
        return True

    def call(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError


# ----- Mock -----

class MockAdapter(LLMAdapter):
    """Offline adapter - cho test và fallback khi không có LLM thật."""
    PROVIDER = LLMProvider.MOCK
    DEFAULT_MODEL = "mock"

    def __init__(
        self,
        canned_responses: Optional[Dict[str, str]] = None,
        default_response: str = '{"mock": true}',
    ):
        self.canned_responses = canned_responses or {}
        self.default_response = default_response

    def call(self, request: LLMRequest) -> LLMResponse:
        t0 = time.perf_counter()
        response_text = self.default_response
        for key, text in self.canned_responses.items():
            if key in request.prompt:
                response_text = text
                break
        elapsed = (time.perf_counter() - t0) * 1000
        p_tok = len(request.prompt) // 4
        c_tok = len(response_text) // 4
        return LLMResponse(
            provider=self.PROVIDER,
            model=request.model or self.DEFAULT_MODEL,
            raw_text=response_text,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=p_tok + c_tok,
            cost_usd=0.0,
            elapsed_ms=elapsed,
            finish_reason="stop",
        )


# ----- OpenAI -----

class OpenAIAdapter(LLMAdapter):
    PROVIDER = LLMProvider.OPENAI
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key
        if default_model:
            self.DEFAULT_MODEL = default_model
        self._client = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def call(self, request: LLMRequest) -> LLMResponse:
        t0 = time.perf_counter()
        model = request.model or self.DEFAULT_MODEL
        try:
            if not self.is_available():
                raise RuntimeError("openai SDK not installed or api_key missing")
            client = self._get_client()
            messages: List[Dict[str, Any]] = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            if request.json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            if request.stop:
                kwargs["stop"] = request.stop

            response = client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content or ""
            usage = response.usage
            p_tok = usage.prompt_tokens if usage else 0
            c_tok = usage.completion_tokens if usage else 0
            cost = estimate_cost_usd(model, p_tok, c_tok)

            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text=text,
                prompt_tokens=p_tok, completion_tokens=c_tok,
                total_tokens=p_tok + c_tok,
                cost_usd=cost,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                finish_reason=response.choices[0].finish_reason or "stop",
            )
        except Exception as e:
            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text="",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                error=f"{type(e).__name__}: {e}",
            )


# ----- Anthropic -----

class AnthropicAdapter(LLMAdapter):
    PROVIDER = LLMProvider.ANTHROPIC
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key
        if default_model:
            self.DEFAULT_MODEL = default_model
        self._client = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def call(self, request: LLMRequest) -> LLMResponse:
        t0 = time.perf_counter()
        model = request.model or self.DEFAULT_MODEL
        try:
            if not self.is_available():
                raise RuntimeError("anthropic SDK not installed or api_key missing")
            client = self._get_client()
            kwargs: Dict[str, Any] = {
                "model": model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "messages": [{"role": "user", "content": request.prompt}],
            }
            if request.system_prompt:
                kwargs["system"] = request.system_prompt
            if request.stop:
                kwargs["stop_sequences"] = request.stop

            response = client.messages.create(**kwargs)
            text = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text
            usage = getattr(response, "usage", None)
            p_tok = getattr(usage, "input_tokens", 0) if usage else 0
            c_tok = getattr(usage, "output_tokens", 0) if usage else 0
            # Strip version suffix for cost lookup
            model_key = model.split("-2024")[0].split("-2025")[0]
            cost = estimate_cost_usd(model_key, p_tok, c_tok)

            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text=text,
                prompt_tokens=p_tok, completion_tokens=c_tok,
                total_tokens=p_tok + c_tok,
                cost_usd=cost,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                finish_reason=getattr(response, "stop_reason", "stop") or "stop",
            )
        except Exception as e:
            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text="",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                error=f"{type(e).__name__}: {e}",
            )


# ----- Gemini -----

class GeminiAdapter(LLMAdapter):
    PROVIDER = LLMProvider.GEMINI
    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key
        if default_model:
            self.DEFAULT_MODEL = default_model
        self._initialized = False

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import google.generativeai  # noqa: F401
            return True
        except ImportError:
            return False

    def _ensure_init(self):
        if self._initialized:
            return
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self._initialized = True

    def call(self, request: LLMRequest) -> LLMResponse:
        t0 = time.perf_counter()
        model = request.model or self.DEFAULT_MODEL
        try:
            if not self.is_available():
                raise RuntimeError("google-generativeai SDK not installed or api_key missing")
            self._ensure_init()
            import google.generativeai as genai
            gen_config = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
            }
            if request.json_mode:
                gen_config["response_mime_type"] = "application/json"
            gmodel = genai.GenerativeModel(
                model, system_instruction=request.system_prompt,
            )
            response = gmodel.generate_content(
                request.prompt, generation_config=gen_config,
            )
            text = response.text if hasattr(response, "text") else ""
            usage = getattr(response, "usage_metadata", None)
            p_tok = getattr(usage, "prompt_token_count", 0) if usage else 0
            c_tok = getattr(usage, "candidates_token_count", 0) if usage else 0
            cost = estimate_cost_usd(model, p_tok, c_tok)

            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text=text,
                prompt_tokens=p_tok, completion_tokens=c_tok,
                total_tokens=p_tok + c_tok,
                cost_usd=cost,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as e:
            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text="",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                error=f"{type(e).__name__}: {e}",
            )


# ----- Ollama (local) -----

class OllamaAdapter(LLMAdapter):
    PROVIDER = LLMProvider.OLLAMA
    DEFAULT_MODEL = "llama3:8b"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: Optional[str] = None,
    ):
        self.base_url = base_url
        if default_model:
            self.DEFAULT_MODEL = default_model

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def call(self, request: LLMRequest) -> LLMResponse:
        import urllib.error
        import urllib.request
        t0 = time.perf_counter()
        model = request.model or self.DEFAULT_MODEL
        try:
            payload: Dict[str, Any] = {
                "model": model,
                "prompt": request.prompt,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            }
            if request.system_prompt:
                payload["system"] = request.system_prompt
            if request.json_mode:
                payload["format"] = "json"
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            text = data.get("response", "")
            p_tok = data.get("prompt_eval_count", len(request.prompt) // 4)
            c_tok = data.get("eval_count", len(text) // 4)
            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text=text,
                prompt_tokens=p_tok, completion_tokens=c_tok,
                total_tokens=p_tok + c_tok,
                cost_usd=0.0,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as e:
            return LLMResponse(
                provider=self.PROVIDER, model=model,
                raw_text="",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                error=f"{type(e).__name__}: {e}",
            )


# ============================================================
# 4. CACHE
# ============================================================

class LLMResponseCache:
    def __init__(self, max_entries: int = 500):
        self._store: Dict[str, LLMResponse] = {}
        self._order: List[str] = []
        self.max_entries = max_entries

    @staticmethod
    def key_for(request: LLMRequest) -> str:
        payload = {
            "p": request.prompt,
            "s": request.system_prompt,
            "t": round(request.temperature, 2),
            "m": request.model or "",
            "j": request.json_mode,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        k = self.key_for(request)
        return self._store.get(k)

    def put(self, request: LLMRequest, response: LLMResponse) -> None:
        k = self.key_for(request)
        if k not in self._store:
            self._order.append(k)
        self._store[k] = response
        # LRU eviction
        while len(self._order) > self.max_entries:
            evict = self._order.pop(0)
            self._store.pop(evict, None)


# ============================================================
# 5. AUDIT TRAIL
# ============================================================

class LLMAuditTrail:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        request: LLMRequest,
        response: LLMResponse,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry = {
            "ts": _now_iso(),
            "provider": response.provider.value,
            "model": response.model,
            "prompt_preview": request.prompt[:200],
            "system_preview": (request.system_prompt or "")[:100],
            "temperature": request.temperature,
            "response_preview": response.raw_text[:200],
            "response": response.to_dict(),
            "context": context or {},
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


# ============================================================
# 6. MULTI-PROVIDER BROKER
# ============================================================

@dataclass
class BrokerConfig:
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    enable_cache: bool = True
    cache_size: int = 500
    audit_path: Optional[Path] = None
    cost_cap_usd_per_run: float = 5.0              # Hard cap để chặn $
    abort_on_cost_cap: bool = True


class LLMBroker:
    """
    Facade chính. Cách dùng điển hình:
        broker = LLMBroker(
            adapters=[OpenAIAdapter(api_key=...), AnthropicAdapter(api_key=...)],
            config=BrokerConfig(audit_path=Path("./logs/llm_audit.jsonl")),
        )
        # Gọi raw
        response = broker.call(LLMRequest(prompt="..."))
        # Gọi với schema (auto retry)
        outcome = broker.call_with_schema(prompt="...", schema={...})
    """

    def __init__(
        self,
        adapters: Sequence[LLMAdapter],
        config: Optional[BrokerConfig] = None,
        schema_guard: Optional[SchemaGuard] = None,
    ):
        self.adapters = [a for a in adapters if a is not None]
        self.config = config or BrokerConfig()
        self.schema_guard = schema_guard or SchemaGuard()
        self.retry_harness = RetryHarness(
            self.schema_guard, self.config.retry_policy,
        )
        self.cache: Optional[LLMResponseCache] = (
            LLMResponseCache(self.config.cache_size) if self.config.enable_cache else None
        )
        self.audit: Optional[LLMAuditTrail] = (
            LLMAuditTrail(self.config.audit_path) if self.config.audit_path else None
        )
        self._total_cost_usd = 0.0
        self._call_count = 0

    def list_available(self) -> List[str]:
        return [a.PROVIDER.value for a in self.adapters if a.is_available()]

    @property
    def total_cost_usd(self) -> float:
        return round(self._total_cost_usd, 6)

    @property
    def call_count(self) -> int:
        return self._call_count

    def reset_cost_tracking(self) -> None:
        self._total_cost_usd = 0.0
        self._call_count = 0

    # ---- RAW CALL (tries fallback chain) ----

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def call(
        self,
        request: LLMRequest,
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        # Cost cap
        if self.config.abort_on_cost_cap \
                and self._total_cost_usd >= self.config.cost_cap_usd_per_run:
            return LLMResponse(
                provider=LLMProvider.MOCK, model="cost_capped",
                raw_text="",
                error=f"cost_cap_reached: ${self._total_cost_usd:.4f} >= ${self.config.cost_cap_usd_per_run}",
            )

        # Cache hit
        if self.cache:
            cached = self.cache.get(request)
            if cached and cached.ok():
                cached.cached = True
                return cached

        last_response: Optional[LLMResponse] = None
        for adapter in self.adapters:
            if not adapter.is_available():
                continue
            response = adapter.call(request)
            self._call_count += 1
            self._total_cost_usd += response.cost_usd
            last_response = response
            if self.audit:
                try:
                    self.audit.append(request, response, context)
                except Exception:
                    pass
            if response.ok():
                if self.cache:
                    self.cache.put(request, response)
                return response

        # All adapters failed
        if last_response is None:
            last_response = LLMResponse(
                provider=LLMProvider.MOCK, model="no_adapter_available",
                raw_text="",
                error="no_adapter_available_or_all_disabled",
            )
        return last_response

    # ---- CALL WITH SCHEMA (retry + validation) ----

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def call_with_schema(
        self,
        prompt: str,
        schema: Mapping[str, Any],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        initial_temperature: float = 0.2,
        context: Optional[Dict[str, Any]] = None,
    ) -> RetryOutcome:
        """
        Convenience: gọi LLM + validate schema + retry (temperature decay).
        Trả RetryOutcome với final_payload là dict/list đã validate.
        """
        original_temp = self.config.retry_policy.initial_temperature
        self.config.retry_policy.initial_temperature = initial_temperature
        try:
            def fn(prompt_text: str, temperature: float) -> str:
                req = LLMRequest(
                    prompt=prompt_text,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                    json_mode=True,
                )
                resp = self.call(req, context=context)
                if not resp.ok():
                    raise RuntimeError(resp.error or "empty_response")
                return resp.raw_text

            outcome = self.retry_harness.call_with_retry(fn, prompt, schema)
            return outcome
        finally:
            self.config.retry_policy.initial_temperature = original_temp

    def summary(self) -> Dict[str, Any]:
        return {
            "version": LLM_BROKER_VERSION,
            "total_calls": self._call_count,
            "total_cost_usd": self.total_cost_usd,
            "cost_cap_usd": self.config.cost_cap_usd_per_run,
            "adapters_configured": len(self.adapters),
            "adapters_available": self.list_available(),
            "cache_enabled": self.cache is not None,
            "audit_enabled": self.audit is not None,
        }


# ============================================================
# 7. SANITY CHECK
# ============================================================

def llm_broker_sanity_check(tmp_path: Optional[Path] = None) -> Dict[str, bool]:
    import tempfile
    checks: Dict[str, bool] = {}

    # Mock adapter with canned
    mock = MockAdapter(canned_responses={
        "user_schema": '{"name": "Alice", "age": 30}',
    })
    checks["mock_available"] = mock.is_available()

    # Raw call
    resp = mock.call(LLMRequest(prompt="user_schema please"))
    checks["mock_responds"] = resp.ok() and "Alice" in resp.raw_text

    # Broker
    tmp = tmp_path or Path(tempfile.mkdtemp(prefix="llm_broker_"))
    broker = LLMBroker(
        adapters=[mock],
        config=BrokerConfig(
            audit_path=tmp / "llm_audit.jsonl",
            enable_cache=True,
        ),
    )
    resp2 = broker.call(LLMRequest(prompt="user_schema please"))
    checks["broker_call_ok"] = resp2.ok()
    checks["audit_file_created"] = (tmp / "llm_audit.jsonl").exists()

    # Cache hit
    resp3 = broker.call(LLMRequest(prompt="user_schema please"))
    checks["cache_hit"] = resp3.cached is True

    # Schema call
    schema = {
        "type": "object",
        "required": ["name", "age"],
        "properties": {
            "name": {"type": "string"},
            "age":  {"type": "integer", "minimum": 0},
        },
        "additionalProperties": False,
    }
    outcome = broker.call_with_schema(
        prompt="Please generate user_schema matching the schema",
        schema=schema,
    )
    checks["schema_call_success"] = outcome.success
    checks["payload_correct"] = (
        outcome.final_payload is not None
        and outcome.final_payload.get("name") == "Alice"
    )

    # Mock with always-bad response
    bad_mock = MockAdapter(default_response="not json at all")
    broker_bad = LLMBroker(
        adapters=[bad_mock],
        config=BrokerConfig(
            retry_policy=RetryPolicy(max_attempts=2),
            enable_cache=False,
        ),
    )
    outcome_bad = broker_bad.call_with_schema(
        prompt="anything", schema=schema,
    )
    checks["bad_response_fails_gracefully"] = not outcome_bad.success
    checks["retry_count_matches"] = len(outcome_bad.attempts) == 2

    # Cost cap
    broker_capped = LLMBroker(
        adapters=[mock],
        config=BrokerConfig(
            cost_cap_usd_per_run=0.0,    # cap = 0 → chặn ngay
            abort_on_cost_cap=True,
        ),
    )
    # First call passes (cost=0)
    # Force cost to be high
    broker_capped._total_cost_usd = 10.0
    capped_resp = broker_capped.call(LLMRequest(prompt="anything"))
    checks["cost_cap_blocks"] = capped_resp.error is not None and "cost_cap" in (
        capped_resp.error or ""
    )

    # Provider without SDK → gracefully reports unavailable
    openai_no_key = OpenAIAdapter(api_key=None)
    checks["no_key_unavailable"] = not openai_no_key.is_available()

    # Broker với all adapter unavailable
    broker_empty = LLMBroker(adapters=[openai_no_key])
    resp_none = broker_empty.call(LLMRequest(prompt="x"))
    checks["no_adapter_error"] = resp_none.error == "no_adapter_available_or_all_disabled"

    # Summary
    summary = broker.summary()
    checks["summary_has_keys"] = {"total_calls", "total_cost_usd", "adapters_available"} <= set(summary.keys())

    return checks


__all__ = [
    "LLM_BROKER_VERSION",
    "LLMProvider", "COST_TABLE", "estimate_cost_usd",
    "LLMRequest", "LLMResponse",
    "LLMAdapter", "MockAdapter", "OpenAIAdapter",
    "AnthropicAdapter", "GeminiAdapter", "OllamaAdapter",
    "LLMResponseCache", "LLMAuditTrail",
    "BrokerConfig", "LLMBroker",
    "llm_broker_sanity_check",
]
