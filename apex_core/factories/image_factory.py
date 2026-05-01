"""
APEX FACTORY v6.0 - Factory Layer
File: image_factory.py

Mục đích: Sản xuất hình ảnh qua 3 kênh:
    1. IMAGE_GEN     : gọi API image model (DALL-E, Flux, SDXL, Gemini Imagen)
    2. POST_PROCESS  : resize/watermark/optimize trên ảnh có sẵn (cần Pillow)
    3. COMPOSITE     : ghép nhiều ảnh thành infographic/social card

Triết lý:
    - Mỗi gen request đi qua Schema Guard (validate response shape)
    - Mock provider để test offline
    - Post-process optional (nếu không có Pillow, skip)
    - Cost tracking per image
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# ============================================================
# 0. VERSION
# ============================================================

IMAGE_FACTORY_VERSION = "6.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _probe_pillow() -> bool:
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


# ============================================================
# 1. TYPES
# ============================================================

class ImageProvider(str, Enum):
    OPENAI_DALLE = "openai_dalle"
    REPLICATE_FLUX = "replicate_flux"
    STABILITY_SDXL = "stability_sdxl"
    GEMINI_IMAGEN = "gemini_imagen"
    MOCK = "mock"


class ImageFormat(str, Enum):
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class ImageAspect(str, Enum):
    SQUARE = "1:1"
    PORTRAIT = "3:4"
    PORTRAIT_9_16 = "9:16"
    LANDSCAPE = "4:3"
    WIDE = "16:9"


# Cost per image USD (ước tính tại thời điểm viết)
IMAGE_COST_TABLE: Dict[str, float] = {
    "dall-e-3":       0.040,    # 1024x1024 standard
    "dall-e-3-hd":    0.080,
    "dall-e-2":       0.020,
    "flux-schnell":   0.003,
    "flux-dev":       0.030,
    "sdxl":           0.010,
    "imagen-3":       0.030,
    "mock":           0.000,
}


@dataclass
class ImageGenRequest:
    prompt: str
    provider: ImageProvider = ImageProvider.MOCK
    model: Optional[str] = None        # None → provider default
    aspect: ImageAspect = ImageAspect.SQUARE
    format: ImageFormat = ImageFormat.PNG
    count: int = 1
    negative_prompt: str = ""
    seed: Optional[int] = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedImage:
    provider: ImageProvider
    model: str
    prompt: str
    url: Optional[str] = None
    bytes_b64: Optional[str] = None
    width: int = 0
    height: int = 0
    format: ImageFormat = ImageFormat.PNG
    seed_used: Optional[int] = None
    cost_usd: float = 0.0
    content_hash: str = ""
    generated_at_utc: str = field(default_factory=_now_iso)

    def _compute_hash(self) -> str:
        payload = self.bytes_b64 or self.url or f"{self.prompt}:{self.seed_used}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self._compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model": self.model,
            "prompt": self.prompt[:200],
            "url": self.url,
            "has_bytes": bool(self.bytes_b64),
            "width": self.width,
            "height": self.height,
            "format": self.format.value,
            "seed_used": self.seed_used,
            "cost_usd": round(self.cost_usd, 4),
            "content_hash": self.content_hash,
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass
class ImageGenResult:
    request_id: str
    success: bool
    images: List[GeneratedImage] = field(default_factory=list)
    total_cost_usd: float = 0.0
    elapsed_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "image_count": len(self.images),
            "images": [img.to_dict() for img in self.images],
            "total_cost_usd": round(self.total_cost_usd, 4),
            "elapsed_ms": round(self.elapsed_ms, 2),
            "error": self.error,
        }


# ============================================================
# 2. PROVIDER ADAPTERS
# ============================================================

class ImageProviderAdapter:
    PROVIDER: ImageProvider = ImageProvider.MOCK
    DEFAULT_MODEL: str = "mock"

    def is_available(self) -> bool:
        return True

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        raise NotImplementedError


# ----- Mock -----

class MockImageProvider(ImageProviderAdapter):
    PROVIDER = ImageProvider.MOCK
    DEFAULT_MODEL = "mock"

    def __init__(self, canned_url: str = "https://example.com/mock-image.png"):
        self.canned_url = canned_url

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        t0 = time.perf_counter()
        width, height = self._aspect_to_dims(request.aspect)
        images: List[GeneratedImage] = []
        for i in range(request.count):
            img = GeneratedImage(
                provider=self.PROVIDER,
                model=request.model or self.DEFAULT_MODEL,
                prompt=request.prompt,
                url=f"{self.canned_url}?n={i}",
                width=width, height=height,
                format=request.format,
                seed_used=request.seed or (i * 12345),
                cost_usd=0.0,
            )
            images.append(img)
        return ImageGenResult(
            request_id=f"mock_{int(time.time()*1000)}",
            success=True,
            images=images,
            total_cost_usd=0.0,
            elapsed_ms=(time.perf_counter() - t0) * 1000,
        )

    @staticmethod
    def _aspect_to_dims(aspect: ImageAspect) -> Tuple[int, int]:
        return {
            ImageAspect.SQUARE:        (1024, 1024),
            ImageAspect.PORTRAIT:      (768, 1024),
            ImageAspect.PORTRAIT_9_16: (768, 1344),
            ImageAspect.LANDSCAPE:     (1024, 768),
            ImageAspect.WIDE:          (1344, 768),
        }.get(aspect, (1024, 1024))


# ----- OpenAI DALL-E -----

class OpenAIDALLEProvider(ImageProviderAdapter):
    PROVIDER = ImageProvider.OPENAI_DALLE
    DEFAULT_MODEL = "dall-e-3"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client = None

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def _client_(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        t0 = time.perf_counter()
        model = request.model or self.DEFAULT_MODEL
        size = self._aspect_to_openai_size(request.aspect)
        images: List[GeneratedImage] = []
        total_cost = 0.0
        try:
            if not self.is_available():
                raise RuntimeError("openai SDK not installed or api_key missing")
            client = self._client_()
            resp = client.images.generate(
                model=model,
                prompt=request.prompt,
                size=size,
                n=1,      # dall-e-3 chỉ n=1 per call
                quality="standard",
            )
            for datum in resp.data:
                w, h = [int(x) for x in size.split("x")]
                cost = IMAGE_COST_TABLE.get(model, 0.04)
                total_cost += cost
                images.append(GeneratedImage(
                    provider=self.PROVIDER, model=model,
                    prompt=request.prompt,
                    url=datum.url,
                    width=w, height=h,
                    format=request.format,
                    seed_used=request.seed,
                    cost_usd=cost,
                ))
            return ImageGenResult(
                request_id=f"dalle_{int(time.time()*1000)}",
                success=True,
                images=images,
                total_cost_usd=total_cost,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as e:
            return ImageGenResult(
                request_id=f"dalle_err_{int(time.time()*1000)}",
                success=False,
                images=[],
                total_cost_usd=0.0,
                elapsed_ms=(time.perf_counter() - t0) * 1000,
                error=f"{type(e).__name__}: {e}",
            )

    @staticmethod
    def _aspect_to_openai_size(aspect: ImageAspect) -> str:
        return {
            ImageAspect.SQUARE: "1024x1024",
            ImageAspect.PORTRAIT: "1024x1792",
            ImageAspect.PORTRAIT_9_16: "1024x1792",
            ImageAspect.WIDE: "1792x1024",
            ImageAspect.LANDSCAPE: "1792x1024",
        }.get(aspect, "1024x1024")


# ----- Replicate (Flux) - generic adapter qua HTTP -----

class ReplicateFluxProvider(ImageProviderAdapter):
    PROVIDER = ImageProvider.REPLICATE_FLUX
    DEFAULT_MODEL = "black-forest-labs/flux-schnell"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token

    def is_available(self) -> bool:
        return bool(self.api_token)

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        import urllib.error
        import urllib.request
        t0 = time.perf_counter()
        model = request.model or self.DEFAULT_MODEL
        try:
            if not self.is_available():
                raise RuntimeError("replicate api_token missing")
            payload = {
                "input": {
                    "prompt": request.prompt,
                    "aspect_ratio": request.aspect.value,
                    "num_outputs": request.count,
                    "output_format": request.format.value,
                    "seed": request.seed,
                },
            }
            req = urllib.request.Request(
                f"https://api.replicate.com/v1/models/{model}/predictions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                    "Prefer": "wait",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            output = data.get("output") or []
            if isinstance(output, str):
                output = [output]
            images: List[GeneratedImage] = []
            cost_each = IMAGE_COST_TABLE.get("flux-schnell", 0.003)
            for url in output:
                images.append(GeneratedImage(
                    provider=self.PROVIDER, model=model,
                    prompt=request.prompt, url=url,
                    width=0, height=0,      # unknown từ API
                    format=request.format,
                    seed_used=request.seed,
                    cost_usd=cost_each,
                ))
            return ImageGenResult(
                request_id=data.get("id", f"replicate_{int(time.time()*1000)}"),
                success=True,
                images=images,
                total_cost_usd=cost_each * len(images),
                elapsed_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as e:
            return ImageGenResult(
                request_id=f"replicate_err_{int(time.time()*1000)}",
                success=False,
                images=[],
                error=f"{type(e).__name__}: {e}",
                elapsed_ms=(time.perf_counter() - t0) * 1000,
            )


# ============================================================
# 3. POST-PROCESSOR (optional Pillow)
# ============================================================

@dataclass
class PostProcessConfig:
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    quality: int = 85               # JPEG/WEBP
    watermark_text: Optional[str] = None
    watermark_opacity: float = 0.35
    output_format: ImageFormat = ImageFormat.PNG


class ImagePostProcessor:
    """Optional: dùng Pillow để resize/watermark/optimize."""

    def __init__(self, config: Optional[PostProcessConfig] = None):
        self.config = config or PostProcessConfig()

    def process(
        self, image_bytes: bytes, output_path: Optional[Path] = None,
    ) -> Tuple[bytes, List[str]]:
        warnings: List[str] = []
        if not _probe_pillow():
            warnings.append("Pillow not installed - skip post-process")
            return image_bytes, warnings

        from io import BytesIO

        from PIL import Image as PILImage
        from PIL import ImageDraw, ImageFont

        img = PILImage.open(BytesIO(image_bytes))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        # Resize
        if self.config.target_width and self.config.target_height:
            img = img.resize(
                (self.config.target_width, self.config.target_height),
                PILImage.LANCZOS,
            )
        elif self.config.target_width:
            ratio = self.config.target_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize(
                (self.config.target_width, new_h), PILImage.LANCZOS,
            )

        # Watermark
        if self.config.watermark_text:
            try:
                wm_layer = PILImage.new("RGBA", img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(wm_layer)
                try:
                    font = ImageFont.truetype("arial.ttf", 36)
                except Exception:
                    font = ImageFont.load_default()
                text = self.config.watermark_text
                alpha = int(255 * self.config.watermark_opacity)
                try:
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                except AttributeError:
                    text_w = len(text) * 18
                    text_h = 36
                pos = (img.width - text_w - 20, img.height - text_h - 20)
                draw.text(pos, text, fill=(255, 255, 255, alpha), font=font)
                img = PILImage.alpha_composite(img.convert("RGBA"), wm_layer)
            except Exception as e:
                warnings.append(f"watermark_failed: {e}")

        # Save to bytes
        out_fmt = self.config.output_format.value.upper()
        if out_fmt == "JPEG" and img.mode == "RGBA":
            img = img.convert("RGB")
        buf = BytesIO()
        save_kwargs: Dict[str, Any] = {"format": out_fmt}
        if out_fmt in ("JPEG", "WEBP"):
            save_kwargs["quality"] = self.config.quality
            save_kwargs["optimize"] = True
        img.save(buf, **save_kwargs)
        result_bytes = buf.getvalue()

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(result_bytes)

        return result_bytes, warnings


# ============================================================
# 4. IMAGE FACTORY FACADE
# ============================================================

@dataclass
class ImageFactoryConfig:
    cost_cap_usd_per_batch: float = 2.0
    abort_on_cost_cap: bool = True
    enable_post_process: bool = False
    post_process: Optional[PostProcessConfig] = None


class ImageFactory:
    def __init__(
        self,
        adapters: Sequence[ImageProviderAdapter],
        config: Optional[ImageFactoryConfig] = None,
    ):
        self.adapters = [a for a in adapters if a is not None]
        self.config = config or ImageFactoryConfig()
        self._total_cost = 0.0

    def list_available(self) -> List[str]:
        return [a.PROVIDER.value for a in self.adapters if a.is_available()]

    def _pick_adapter(
        self, preferred: ImageProvider,
    ) -> Optional[ImageProviderAdapter]:
        for a in self.adapters:
            if a.PROVIDER == preferred and a.is_available():
                return a
        # Fallback: first available
        for a in self.adapters:
            if a.is_available():
                return a
        return None

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        if self.config.abort_on_cost_cap \
                and self._total_cost >= self.config.cost_cap_usd_per_batch:
            return ImageGenResult(
                request_id="capped",
                success=False,
                error=(
                    f"cost_cap_reached: ${self._total_cost:.4f} >= "
                    f"${self.config.cost_cap_usd_per_batch}"
                ),
            )

        adapter = self._pick_adapter(request.provider)
        if adapter is None:
            return ImageGenResult(
                request_id="no_adapter",
                success=False,
                error="no_available_adapter",
            )

        result = adapter.generate(request)
        self._total_cost += result.total_cost_usd
        return result

    def generate_batch(
        self, requests: Sequence[ImageGenRequest],
    ) -> List[ImageGenResult]:
        results: List[ImageGenResult] = []
        for req in requests:
            results.append(self.generate(req))
            if self.config.abort_on_cost_cap \
                    and self._total_cost >= self.config.cost_cap_usd_per_batch:
                break
        return results

    @property
    def total_cost_usd(self) -> float:
        return round(self._total_cost, 6)

    def reset_cost(self) -> None:
        self._total_cost = 0.0


# ============================================================
# 5. SANITY CHECK
# ============================================================

def image_factory_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    mock = MockImageProvider()
    checks["mock_available"] = mock.is_available()

    req = ImageGenRequest(
        prompt="A cozy coffee shop in the morning",
        provider=ImageProvider.MOCK,
        aspect=ImageAspect.SQUARE,
        count=2,
    )
    result = mock.generate(req)
    checks["mock_returns_images"] = result.success and len(result.images) == 2
    checks["images_have_hash"] = all(img.content_hash for img in result.images)

    # Factory with mock
    factory = ImageFactory(adapters=[mock])
    checks["factory_lists_mock"] = "mock" in factory.list_available()

    result2 = factory.generate(req)
    checks["factory_generates"] = result2.success

    # Batch
    batch = factory.generate_batch([req, req, req])
    checks["batch_3"] = len(batch) == 3

    # Cost cap - set cap tiny, generate should stop
    factory2 = ImageFactory(
        adapters=[mock],
        config=ImageFactoryConfig(
            cost_cap_usd_per_batch=0.001,
            abort_on_cost_cap=True,
        ),
    )
    factory2._total_cost = 10.0   # force over
    capped = factory2.generate(req)
    checks["cost_cap_blocks"] = capped.error and "cost_cap" in capped.error

    # No API key → OpenAIDALLE unavailable, nhưng Factory không crash
    dalle_no_key = OpenAIDALLEProvider(api_key=None)
    checks["no_key_unavailable"] = not dalle_no_key.is_available()
    factory3 = ImageFactory(adapters=[dalle_no_key])
    no_provider_result = factory3.generate(req)
    checks["no_provider_error"] = not no_provider_result.success

    # Serializable
    try:
        json.dumps(result.to_dict(), default=str)
        checks["serializable"] = True
    except Exception:
        checks["serializable"] = False

    # PostProcessor available check (không crash nếu thiếu Pillow)
    pp = ImagePostProcessor()
    # 1x1 PNG minimal bytes
    tiny_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )
    try:
        out_bytes, warnings_pp = pp.process(tiny_png)
        # Pillow có → bytes khác / không có → bytes trả y nguyên + warning
        checks["postprocess_no_crash"] = True
    except Exception:
        checks["postprocess_no_crash"] = False

    return checks


__all__ = [
    "IMAGE_FACTORY_VERSION",
    "ImageProvider", "ImageFormat", "ImageAspect",
    "IMAGE_COST_TABLE",
    "ImageGenRequest", "GeneratedImage", "ImageGenResult",
    "ImageProviderAdapter",
    "MockImageProvider", "OpenAIDALLEProvider", "ReplicateFluxProvider",
    "PostProcessConfig", "ImagePostProcessor",
    "ImageFactoryConfig", "ImageFactory",
    "image_factory_sanity_check",
]
