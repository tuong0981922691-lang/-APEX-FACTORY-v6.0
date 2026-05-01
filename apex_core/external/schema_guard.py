"""
APEX FACTORY v6.0 - External Integration Layer
File: schema_guard.py

Mục đích: JSON Schema validator đầy đủ + retry harness cho Borrowing Protocol.
    Nâng cấp SchemaGuard tối thiểu của Phase 1 (nhúng trong b6_commander.py).

Hỗ trợ JSON Schema subset:
    - type: object, array, string, number, integer, boolean, null
    - object: required, properties, additionalProperties, patternProperties
    - array: items, minItems, maxItems, uniqueItems
    - string: minLength, maxLength, pattern, enum, const, format (subset)
    - number/integer: minimum, maximum, exclusiveMinimum/Maximum, multipleOf
    - oneOf / anyOf / allOf / not
    - $ref nội bộ (#/definitions/Foo)

Triết lý NT5 + NT6:
    LLM output = không tin. Schema Guard = hàng rào thép.
    Mọi sai lệch nhỏ nhất cũng reject và retry.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

# ============================================================
# 0. VERSION
# ============================================================

SCHEMA_GUARD_VERSION = "6.0.0"


# ============================================================
# 1. ERRORS
# ============================================================

class SchemaGuardError(Exception):
    """Base error với JSON path tường minh."""

    def __init__(self, message: str, path: str = "$", schema_hint: str = ""):
        self.message = message
        self.path = path
        self.schema_hint = schema_hint
        super().__init__(f"[{path}] {message}" + (f" | schema: {schema_hint}" if schema_hint else ""))


class MaxRetriesExceeded(Exception):
    def __init__(self, attempts: int, last_error: str):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Max retries ({attempts}) exceeded. Last error: {last_error}")


# ============================================================
# 2. FORMAT CHECKERS (subset)
# ============================================================

FORMAT_CHECKERS: Dict[str, Callable[[str], bool]] = {
    "email":     lambda s: bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", s)),
    "uri":       lambda s: bool(re.match(r"^[a-z][a-z0-9+.-]*:", s, re.IGNORECASE)),
    "url":       lambda s: bool(re.match(r"^https?://", s, re.IGNORECASE)),
    "uuid":      lambda s: bool(re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s, re.IGNORECASE
    )),
    "date":      lambda s: bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s)),
    "date-time": lambda s: bool(re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", s
    )),
    "ipv4":      lambda s: bool(re.match(
        r"^(\d{1,3}\.){3}\d{1,3}$", s
    )) and all(0 <= int(p) <= 255 for p in s.split(".") if p.isdigit()),
    "hex-color": lambda s: bool(re.match(r"^#[0-9A-Fa-f]{3,8}$", s)),
}


# ============================================================
# 3. VALIDATOR
# ============================================================

@dataclass
class ValidationTrace:
    path: str
    keyword: str
    reason: str


class JSONSchemaValidator:
    """
    Validator subset JSON Schema. Thuần Python, không dependency.
    """

    def __init__(
        self,
        root_schema: Optional[Mapping[str, Any]] = None,
        strict_additional_props: bool = True,
    ):
        self.root_schema = dict(root_schema) if root_schema else {}
        self.strict_additional_props = strict_additional_props

    # ----- Public API -----

    def validate(
        self, instance: Any, schema: Mapping[str, Any],
    ) -> List[ValidationTrace]:
        """Trả list trace. Rỗng = pass."""
        traces: List[ValidationTrace] = []
        self._validate(instance, dict(schema), "$", traces)
        return traces

    def assert_valid(self, instance: Any, schema: Mapping[str, Any]) -> None:
        """Raise SchemaGuardError nếu không pass."""
        traces = self.validate(instance, schema)
        if traces:
            first = traces[0]
            schema_hint = json.dumps(
                {k: v for k, v in schema.items() if k in ("type", "required", "enum")},
                ensure_ascii=False,
            )
            raise SchemaGuardError(
                message=f"{first.keyword}: {first.reason}",
                path=first.path,
                schema_hint=schema_hint,
            )

    # ----- Core dispatcher -----

    def _validate(
        self,
        instance: Any,
        schema: Dict[str, Any],
        path: str,
        traces: List[ValidationTrace],
    ) -> None:
        # $ref first
        if "$ref" in schema:
            ref_schema = self._resolve_ref(schema["$ref"])
            if ref_schema is None:
                traces.append(ValidationTrace(path, "$ref", f"cannot resolve {schema['$ref']}"))
                return
            self._validate(instance, dict(ref_schema), path, traces)
            return

        # Combinators
        for key in ("allOf", "anyOf", "oneOf"):
            if key in schema:
                self._apply_combinator(instance, schema[key], key, path, traces)

        if "not" in schema:
            sub_traces: List[ValidationTrace] = []
            self._validate(instance, dict(schema["not"]), path, sub_traces)
            if not sub_traces:
                traces.append(ValidationTrace(path, "not", "instance matched forbidden schema"))

        # const
        if "const" in schema:
            if instance != schema["const"]:
                traces.append(ValidationTrace(
                    path, "const", f"expected {schema['const']!r}, got {instance!r}"
                ))

        # enum
        if "enum" in schema:
            if instance not in schema["enum"]:
                traces.append(ValidationTrace(
                    path, "enum",
                    f"value {instance!r} not in {schema['enum']}",
                ))

        # type dispatch
        expected_type = schema.get("type")
        if expected_type is not None:
            types = expected_type if isinstance(expected_type, list) else [expected_type]
            if not any(self._matches_type(instance, t) for t in types):
                traces.append(ValidationTrace(
                    path, "type",
                    f"expected {expected_type}, got {self._python_type(instance)}",
                ))
                return    # type mismatch → không kiểm tiếp keyword phụ

            # Type-specific keywords
            if "object" in types and isinstance(instance, dict):
                self._validate_object(instance, schema, path, traces)
            if "array" in types and isinstance(instance, list):
                self._validate_array(instance, schema, path, traces)
            if "string" in types and isinstance(instance, str):
                self._validate_string(instance, schema, path, traces)
            if ("number" in types or "integer" in types) \
                    and isinstance(instance, (int, float)) and not isinstance(instance, bool):
                self._validate_number(instance, schema, path, traces,
                                      is_integer="integer" in types and "number" not in types)

    def _matches_type(self, instance: Any, type_name: str) -> bool:
        if type_name == "null":
            return instance is None
        if type_name == "boolean":
            return isinstance(instance, bool)
        if type_name == "integer":
            return isinstance(instance, int) and not isinstance(instance, bool)
        if type_name == "number":
            return isinstance(instance, (int, float)) and not isinstance(instance, bool)
        if type_name == "string":
            return isinstance(instance, str)
        if type_name == "array":
            return isinstance(instance, list)
        if type_name == "object":
            return isinstance(instance, dict)
        return False

    def _python_type(self, instance: Any) -> str:
        if instance is None:      return "null"
        if isinstance(instance, bool): return "boolean"
        if isinstance(instance, int): return "integer"
        if isinstance(instance, float): return "number"
        if isinstance(instance, str): return "string"
        if isinstance(instance, list): return "array"
        if isinstance(instance, dict): return "object"
        return type(instance).__name__

    # ----- Type-specific validators -----

    def _validate_object(
        self, instance: Dict[str, Any], schema: Dict[str, Any],
        path: str, traces: List[ValidationTrace],
    ) -> None:
        # required
        for req in schema.get("required", []):
            if req not in instance:
                traces.append(ValidationTrace(
                    f"{path}.{req}", "required", "missing required key"
                ))

        # properties
        properties = schema.get("properties", {})
        for key, value in instance.items():
            key_path = f"{path}.{key}"
            if key in properties:
                self._validate(value, dict(properties[key]), key_path, traces)
                continue

            # patternProperties
            matched_pattern = False
            for pattern, sub_schema in schema.get("patternProperties", {}).items():
                if re.search(pattern, key):
                    matched_pattern = True
                    self._validate(value, dict(sub_schema), key_path, traces)

            if not matched_pattern and "properties" in schema:
                # additionalProperties
                ap = schema.get("additionalProperties", True)
                if ap is False and self.strict_additional_props:
                    traces.append(ValidationTrace(
                        key_path, "additionalProperties",
                        f"key '{key}' not allowed",
                    ))
                elif isinstance(ap, dict):
                    self._validate(value, ap, key_path, traces)

        # minProperties / maxProperties
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            traces.append(ValidationTrace(
                path, "minProperties",
                f"{len(instance)} < {schema['minProperties']}",
            ))
        if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
            traces.append(ValidationTrace(
                path, "maxProperties",
                f"{len(instance)} > {schema['maxProperties']}",
            ))

    def _validate_array(
        self, instance: List[Any], schema: Dict[str, Any],
        path: str, traces: List[ValidationTrace],
    ) -> None:
        if "minItems" in schema and len(instance) < schema["minItems"]:
            traces.append(ValidationTrace(
                path, "minItems",
                f"{len(instance)} < {schema['minItems']}",
            ))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            traces.append(ValidationTrace(
                path, "maxItems",
                f"{len(instance)} > {schema['maxItems']}",
            ))
        if schema.get("uniqueItems") is True:
            # Dùng JSON-serialize để so sánh deep
            seen: List[str] = []
            for i, item in enumerate(instance):
                key = json.dumps(item, sort_keys=True, default=str)
                if key in seen:
                    traces.append(ValidationTrace(
                        f"{path}[{i}]", "uniqueItems",
                        "duplicate value",
                    ))
                seen.append(key)

        items_schema = schema.get("items")
        if items_schema:
            if isinstance(items_schema, list):
                # Tuple validation
                for i, item in enumerate(instance):
                    if i < len(items_schema):
                        self._validate(item, dict(items_schema[i]), f"{path}[{i}]", traces)
            else:
                for i, item in enumerate(instance):
                    self._validate(item, dict(items_schema), f"{path}[{i}]", traces)

    def _validate_string(
        self, instance: str, schema: Dict[str, Any],
        path: str, traces: List[ValidationTrace],
    ) -> None:
        if "minLength" in schema and len(instance) < schema["minLength"]:
            traces.append(ValidationTrace(
                path, "minLength",
                f"length {len(instance)} < {schema['minLength']}",
            ))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            traces.append(ValidationTrace(
                path, "maxLength",
                f"length {len(instance)} > {schema['maxLength']}",
            ))
        if "pattern" in schema:
            try:
                if not re.search(schema["pattern"], instance):
                    traces.append(ValidationTrace(
                        path, "pattern",
                        f"does not match {schema['pattern']!r}",
                    ))
            except re.error:
                traces.append(ValidationTrace(
                    path, "pattern", "invalid regex in schema",
                ))
        if "format" in schema:
            checker = FORMAT_CHECKERS.get(schema["format"])
            if checker and not checker(instance):
                traces.append(ValidationTrace(
                    path, "format",
                    f"does not match format {schema['format']!r}",
                ))

    def _validate_number(
        self, instance: Union[int, float], schema: Dict[str, Any],
        path: str, traces: List[ValidationTrace],
        is_integer: bool = False,
    ) -> None:
        if is_integer and not isinstance(instance, int):
            traces.append(ValidationTrace(
                path, "type", "expected integer, got number",
            ))
            return
        if "minimum" in schema and instance < schema["minimum"]:
            traces.append(ValidationTrace(
                path, "minimum", f"{instance} < {schema['minimum']}",
            ))
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            traces.append(ValidationTrace(
                path, "exclusiveMinimum", f"{instance} <= {schema['exclusiveMinimum']}",
            ))
        if "maximum" in schema and instance > schema["maximum"]:
            traces.append(ValidationTrace(
                path, "maximum", f"{instance} > {schema['maximum']}",
            ))
        if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
            traces.append(ValidationTrace(
                path, "exclusiveMaximum", f"{instance} >= {schema['exclusiveMaximum']}",
            ))
        if "multipleOf" in schema:
            m = schema["multipleOf"]
            if m <= 0 or (isinstance(instance, float) and abs(instance % m) > 1e-9) \
                    or (isinstance(instance, int) and instance % m != 0):
                traces.append(ValidationTrace(
                    path, "multipleOf",
                    f"{instance} not multiple of {m}",
                ))

    # ----- Combinators -----

    def _apply_combinator(
        self, instance: Any, sub_schemas: Sequence[Mapping[str, Any]],
        keyword: str, path: str, traces: List[ValidationTrace],
    ) -> None:
        matches = 0
        all_sub_traces: List[List[ValidationTrace]] = []
        for i, sub in enumerate(sub_schemas):
            sub_traces: List[ValidationTrace] = []
            self._validate(instance, dict(sub), f"{path}", sub_traces)
            all_sub_traces.append(sub_traces)
            if not sub_traces:
                matches += 1

        if keyword == "allOf":
            for i, st in enumerate(all_sub_traces):
                traces.extend(st)
        elif keyword == "anyOf":
            if matches == 0:
                traces.append(ValidationTrace(
                    path, "anyOf", f"no sub-schema matched ({len(sub_schemas)} tried)",
                ))
        elif keyword == "oneOf":
            if matches != 1:
                traces.append(ValidationTrace(
                    path, "oneOf",
                    f"expected exactly 1 match, got {matches}",
                ))

    # ----- $ref resolver -----

    def _resolve_ref(self, ref: str) -> Optional[Mapping[str, Any]]:
        if not ref.startswith("#/"):
            return None
        parts = ref[2:].split("/")
        node: Any = self.root_schema
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        return node if isinstance(node, dict) else None


# ============================================================
# 4. SCHEMA GUARD FACADE
# ============================================================

@dataclass
class GuardResult:
    passed: bool
    traces: List[ValidationTrace]
    attempt: int
    repaired: bool = False
    raw_text_preview: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "attempt": self.attempt,
            "repaired": self.repaired,
            "traces": [asdict(t) for t in self.traces[:10]],
            "raw_text_preview": self.raw_text_preview[:500],
        }


class SchemaGuard:
    """High-level facade: parse + validate + retry."""

    def __init__(
        self,
        strict_additional_props: bool = True,
    ):
        self.strict_additional_props = strict_additional_props

    def parse_and_validate(
        self, raw_text: str, schema: Mapping[str, Any],
    ) -> GuardResult:
        """
        Parse raw_text → JSON → validate.
        Nếu parse fail: thử extract JSON từ trong code fence (```json ... ```).
        """
        parsed, repaired = self._robust_json_parse(raw_text)
        if parsed is None:
            return GuardResult(
                passed=False,
                traces=[ValidationTrace(
                    "$", "parse", "cannot parse as JSON even with repair",
                )],
                attempt=1,
                repaired=repaired,
                raw_text_preview=raw_text[:500],
            )

        validator = JSONSchemaValidator(
            root_schema=schema,
            strict_additional_props=self.strict_additional_props,
        )
        traces = validator.validate(parsed, schema)
        return GuardResult(
            passed=len(traces) == 0,
            traces=traces,
            attempt=1,
            repaired=repaired,
            raw_text_preview=raw_text[:500],
        )

    def _robust_json_parse(self, raw: str) -> Tuple[Optional[Any], bool]:
        """
        Thử parse. Nếu fail:
            1. strip markdown fence ```json ... ```
            2. trim tới {.*} hoặc [.*]
            3. try parse lại
        Return (parsed, repaired_bool).
        """
        try:
            return json.loads(raw), False
        except Exception:
            pass

        # Strip code fence
        fence_match = re.search(r"```(?:json)?\s*(.+?)\s*```", raw, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1)), True
            except Exception:
                pass

        # Trim đến dấu { hoặc [
        first_brace = min(
            (raw.find(c) for c in "{[" if raw.find(c) >= 0),
            default=-1,
        )
        last_brace = max(raw.rfind("}"), raw.rfind("]"))
        if 0 <= first_brace < last_brace:
            candidate = raw[first_brace:last_brace + 1]
            try:
                return json.loads(candidate), True
            except Exception:
                pass

        return None, False


# ============================================================
# 5. RETRY HARNESS (temperature decay)
# ============================================================

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    initial_temperature: float = 0.3
    temperature_decay: float = 0.5     # temperature *= decay per retry
    include_previous_error_in_retry: bool = True


@dataclass
class RetryAttempt:
    attempt_index: int
    temperature_used: float
    passed: bool
    error_summary: str = ""
    elapsed_ms: float = 0.0


@dataclass
class RetryOutcome:
    success: bool
    final_payload: Optional[Any]
    attempts: List[RetryAttempt]
    total_calls: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "attempts": [asdict(a) for a in self.attempts],
            "total_calls": self.total_calls,
            "has_payload": self.final_payload is not None,
        }


class RetryHarness:
    """
    Gọi LLM với schema guard + retry + temperature decay.

    callable_fn signature: (prompt, temperature) -> raw_text
    """

    def __init__(
        self,
        guard: SchemaGuard,
        policy: Optional[RetryPolicy] = None,
    ):
        self.guard = guard
        self.policy = policy or RetryPolicy()

    def call_with_retry(
        self,
        callable_fn: Callable[[str, float], str],
        prompt: str,
        schema: Mapping[str, Any],
    ) -> RetryOutcome:
        import time as _time
        attempts: List[RetryAttempt] = []
        temperature = self.policy.initial_temperature
        last_error_summary = ""

        for idx in range(1, self.policy.max_attempts + 1):
            t0 = _time.perf_counter()
            # Augment prompt with last error if retry
            effective_prompt = prompt
            if idx > 1 and last_error_summary \
                    and self.policy.include_previous_error_in_retry:
                effective_prompt = (
                    f"{prompt}\n\n"
                    f"PREVIOUS OUTPUT FAILED validation: {last_error_summary}\n"
                    f"Please output VALID JSON strictly matching the schema. "
                    f"Do NOT wrap in markdown."
                )

            try:
                raw = callable_fn(effective_prompt, temperature)
            except Exception as e:
                attempts.append(RetryAttempt(
                    attempt_index=idx,
                    temperature_used=temperature,
                    passed=False,
                    error_summary=f"call_exception: {type(e).__name__}: {e}",
                    elapsed_ms=(_time.perf_counter() - t0) * 1000,
                ))
                last_error_summary = f"call_exception: {e}"
                temperature *= self.policy.temperature_decay
                continue

            result = self.guard.parse_and_validate(raw, schema)
            elapsed = (_time.perf_counter() - t0) * 1000
            if result.passed:
                parsed, _ = self.guard._robust_json_parse(raw)
                attempts.append(RetryAttempt(
                    attempt_index=idx,
                    temperature_used=temperature,
                    passed=True,
                    elapsed_ms=elapsed,
                ))
                return RetryOutcome(
                    success=True,
                    final_payload=parsed,
                    attempts=attempts,
                    total_calls=idx,
                )

            # Failed → summary + decay
            trace_summary = (
                f"{len(result.traces)} schema errors; "
                f"first: [{result.traces[0].path}] "
                f"{result.traces[0].keyword}: {result.traces[0].reason}"
                if result.traces else "parse_failed"
            )
            last_error_summary = trace_summary
            attempts.append(RetryAttempt(
                attempt_index=idx,
                temperature_used=temperature,
                passed=False,
                error_summary=trace_summary,
                elapsed_ms=elapsed,
            ))
            temperature *= self.policy.temperature_decay

        return RetryOutcome(
            success=False,
            final_payload=None,
            attempts=attempts,
            total_calls=self.policy.max_attempts,
        )


# ============================================================
# 6. SANITY CHECK
# ============================================================

def schema_guard_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    # Valid case
    schema = {
        "type": "object",
        "required": ["name", "age"],
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "minLength": 1, "maxLength": 50},
            "age":  {"type": "integer", "minimum": 0, "maximum": 150},
            "email": {"type": "string", "format": "email"},
        },
    }
    v = JSONSchemaValidator()
    checks["valid_passes"] = len(v.validate(
        {"name": "Alice", "age": 30, "email": "a@b.com"}, schema,
    )) == 0
    checks["missing_required"] = len(v.validate(
        {"name": "Alice"}, schema,
    )) >= 1
    checks["wrong_type"] = len(v.validate(
        {"name": "Alice", "age": "thirty"}, schema,
    )) >= 1
    checks["format_email_bad"] = len(v.validate(
        {"name": "X", "age": 10, "email": "not-email"}, schema,
    )) >= 1
    checks["additional_prop_rejected"] = len(v.validate(
        {"name": "X", "age": 10, "extra": "yo"}, schema,
    )) >= 1

    # enum + const
    schema2 = {
        "type": "object",
        "properties": {
            "status": {"enum": ["draft", "published"]},
            "kind":   {"const": "article"},
        },
    }
    checks["enum_ok"] = len(v.validate(
        {"status": "draft", "kind": "article"}, schema2,
    )) == 0
    checks["enum_bad"] = len(v.validate(
        {"status": "archived", "kind": "article"}, schema2,
    )) >= 1
    checks["const_bad"] = len(v.validate(
        {"status": "draft", "kind": "video"}, schema2,
    )) >= 1

    # oneOf
    schema3 = {
        "oneOf": [
            {"type": "string"},
            {"type": "integer"},
        ],
    }
    checks["oneof_str"] = len(v.validate("hello", schema3)) == 0
    checks["oneof_int"] = len(v.validate(42, schema3)) == 0
    checks["oneof_none"] = len(v.validate(True, schema3)) >= 1   # bool không match

    # Array
    schema4 = {
        "type": "array",
        "minItems": 1, "maxItems": 3,
        "items": {"type": "string", "minLength": 1},
        "uniqueItems": True,
    }
    checks["array_ok"] = len(v.validate(["a", "b"], schema4)) == 0
    checks["array_too_long"] = len(v.validate(["a", "b", "c", "d"], schema4)) >= 1
    checks["array_dup"] = len(v.validate(["x", "x"], schema4)) >= 1

    # Pattern
    schema5 = {"type": "string", "pattern": r"^[a-z]+$"}
    checks["pattern_ok"] = len(v.validate("hello", schema5)) == 0
    checks["pattern_bad"] = len(v.validate("Hello", schema5)) >= 1

    # $ref
    schema_with_ref = {
        "definitions": {
            "Address": {
                "type": "object",
                "required": ["city"],
                "properties": {"city": {"type": "string"}},
            },
        },
        "type": "object",
        "properties": {
            "addr": {"$ref": "#/definitions/Address"},
        },
    }
    v2 = JSONSchemaValidator(root_schema=schema_with_ref)
    checks["ref_ok"] = len(v2.validate(
        {"addr": {"city": "Hanoi"}}, schema_with_ref,
    )) == 0
    checks["ref_bad"] = len(v2.validate(
        {"addr": {"country": "VN"}}, schema_with_ref,
    )) >= 1

    # Robust JSON parse
    guard = SchemaGuard()
    markdown_wrapped = '```json\n{"name": "X", "age": 20}\n```'
    result = guard.parse_and_validate(markdown_wrapped, schema)
    checks["strip_markdown_fence"] = result.repaired and not result.passed or (
        result.passed and result.repaired
    )  # age<0 validation nhưng repaired phải True
    # Actual: schema yêu cầu name+age, age=20 hợp lệ → passed True, repaired True
    checks["markdown_parses_and_passes"] = result.passed

    # Retry harness: fake callable fail 2 lần rồi pass
    call_log: List[Tuple[str, float]] = []
    def fake_llm(prompt: str, temperature: float) -> str:
        call_log.append((prompt, temperature))
        if len(call_log) < 3:
            return "not json"
        return '{"name": "OK", "age": 25}'

    harness = RetryHarness(guard, RetryPolicy(max_attempts=4))
    outcome = harness.call_with_retry(fake_llm, "Make user", schema)
    checks["retry_eventually_passes"] = outcome.success
    checks["retry_total_calls_3"] = outcome.total_calls == 3
    checks["retry_temperature_decayed"] = (
        outcome.attempts[0].temperature_used > outcome.attempts[-1].temperature_used
    )

    # Retry exhaustion
    def always_fail(prompt: str, temperature: float) -> str:
        return "garbage"
    outcome2 = harness.call_with_retry(always_fail, "test", schema)
    checks["retry_exhausts"] = not outcome2.success
    checks["exhaust_count_matches_policy"] = len(outcome2.attempts) == 4

    return checks


__all__ = [
    "SCHEMA_GUARD_VERSION",
    "SchemaGuardError", "MaxRetriesExceeded",
    "FORMAT_CHECKERS",
    "ValidationTrace", "JSONSchemaValidator",
    "GuardResult", "SchemaGuard",
    "RetryPolicy", "RetryAttempt", "RetryOutcome", "RetryHarness",
    "schema_guard_sanity_check",
]
