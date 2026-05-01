"""
APEX FACTORY v6.0 - Foundation Extension
File: ontology_media.py

Mục đích: Ontology cho miền sản xuất video/image/audio. Gương cùng 3 tầng
          như ontology_ui nhưng cho đối tượng media:

    Nguyên tử : FrameToken, AudioSampleToken, VisualToken (color/motion)
    Phân tử   : ShotSpec (sequence frames), AudioTrackSpec, CaptionSpec
    Hợp chất  : SceneGraph (timeline DAG của shots + audio + transitions)

Chú ý Phase ưu tiên: Web → App → Video. Ontology này được khung hóa đầy đủ
       ở Phase 0 để sau này (Phase 6) Factory video không phải rebuild nền.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# 0. VERSION
# ============================================================

ONTOLOGY_MEDIA_VERSION = "6.0.0"
ONTOLOGY_MEDIA_SCHEMA = "apex.factory.media/v6"


# ============================================================
# 1. ENUMS
# ============================================================

class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"
    PRORES = "prores"


class PixelFormat(str, Enum):
    YUV420P = "yuv420p"
    YUV422P = "yuv422p"
    YUV444P = "yuv444p"
    RGBA = "rgba"


class AudioCodec(str, Enum):
    AAC = "aac"
    MP3 = "mp3"
    OPUS = "opus"
    FLAC = "flac"
    PCM_S16LE = "pcm_s16le"


class CameraMotion(str, Enum):
    STATIC = "static"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    ORBIT = "orbit"
    HANDHELD = "handheld"


class TransitionKind(str, Enum):
    CUT = "cut"                 # cắt thẳng
    FADE = "fade"               # mờ dần sang đen/trắng
    CROSS_DISSOLVE = "cross_dissolve"
    WIPE = "wipe"
    SLIDE = "slide"
    ZOOM = "zoom"
    MORPH = "morph"


class MediaDomain(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    MIXED = "mixed"


# ============================================================
# 2. TẦNG NGUYÊN TỬ
# ============================================================

@dataclass(frozen=True)
class Resolution:
    width: int
    height: int

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Resolution must be positive: {self.width}x{self.height}")

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    def is_vertical(self) -> bool:
        return self.height > self.width

    def to_dict(self) -> Dict[str, int]:
        return {"width": self.width, "height": self.height}


# Presets phổ biến
RESOLUTION_HD: Resolution = Resolution(1280, 720)
RESOLUTION_FHD: Resolution = Resolution(1920, 1080)
RESOLUTION_4K: Resolution = Resolution(3840, 2160)
RESOLUTION_REEL_9_16: Resolution = Resolution(1080, 1920)   # Reels/Shorts
RESOLUTION_SQUARE: Resolution = Resolution(1080, 1080)


@dataclass(frozen=True)
class FrameToken:
    """
    1 frame trong video. Đây là "digit 0-9" của ontology media.
    Frame immutable, định danh bằng timestamp_ms chính xác.
    """
    frame_id: str
    timestamp_ms: int                   # ms kể từ đầu video
    resolution: Resolution
    pixel_format: PixelFormat = PixelFormat.YUV420P
    is_keyframe: bool = False
    source_ref: Optional[str] = None    # URL/path ảnh gốc nếu import

    def __post_init__(self):
        if self.timestamp_ms < 0:
            raise ValueError(f"Negative timestamp: {self.timestamp_ms}")


@dataclass(frozen=True)
class AudioSampleToken:
    """Cấu hình 1 đoạn audio - tương đương nguyên tử."""
    sample_id: str
    sample_rate_hz: int = 48000
    channels: int = 2
    bit_depth: int = 16

    def __post_init__(self):
        if self.sample_rate_hz not in (22050, 32000, 44100, 48000, 96000):
            raise ValueError(f"Unusual sample_rate: {self.sample_rate_hz}")
        if self.channels not in (1, 2, 6):
            raise ValueError(f"channels must be 1/2/6: {self.channels}")


@dataclass(frozen=True)
class VisualToken:
    """Token dùng chung cho khung hình - color/motion style."""
    token_id: str
    color_grade: str = "neutral"       # "warm" | "cool" | "neutral" | "bw" | "cinematic"
    film_grain: float = 0.0            # 0..1
    motion_blur: float = 0.0           # 0..1
    exposure_ev: float = 0.0           # -3..+3 stops
    saturation: float = 1.0            # 0..2

    def __post_init__(self):
        for name, val, lo, hi in (
            ("film_grain", self.film_grain, 0.0, 1.0),
            ("motion_blur", self.motion_blur, 0.0, 1.0),
            ("exposure_ev", self.exposure_ev, -3.0, 3.0),
            ("saturation", self.saturation, 0.0, 2.0),
        ):
            if not (lo <= val <= hi):
                raise ValueError(f"{name}={val} out of [{lo},{hi}]")


# ============================================================
# 3. TẦNG PHÂN TỬ
# ============================================================

@dataclass(frozen=True)
class ShotSpec:
    """
    Một "cảnh quay" - sequence frame liên tục cùng camera motion.
    Tương đương '2-digit number' của ontology XSMB.
    """
    shot_id: str
    duration_ms: int
    fps: int                            # 24/30/60
    camera_motion: CameraMotion
    resolution: Resolution
    visual_token_id: Optional[str] = None
    subject_prompt: str = ""            # mô tả chủ thể để image/video model sinh
    reference_image_refs: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.duration_ms <= 0:
            raise ValueError(f"Shot duration must be positive: {self.duration_ms}")
        if self.fps not in (24, 25, 30, 50, 60):
            raise ValueError(f"Unusual fps: {self.fps}")

    @property
    def total_frames(self) -> int:
        return int(round(self.duration_ms * self.fps / 1000))


@dataclass(frozen=True)
class AudioTrackSpec:
    """1 track audio trên timeline."""
    track_id: str
    kind: str                           # "voiceover" | "music" | "sfx" | "ambient"
    source_ref: str                     # path/URL
    start_ms: int = 0
    duration_ms: Optional[int] = None   # None = theo độ dài source
    volume: float = 1.0
    fade_in_ms: int = 0
    fade_out_ms: int = 0
    codec: AudioCodec = AudioCodec.AAC

    def __post_init__(self):
        if self.start_ms < 0:
            raise ValueError(f"Negative start_ms: {self.start_ms}")
        if not (0.0 <= self.volume <= 2.0):
            raise ValueError(f"volume out of [0,2]: {self.volume}")


@dataclass(frozen=True)
class CaptionSpec:
    """1 đoạn caption/subtitle hiển thị lên frame."""
    caption_id: str
    text: str
    start_ms: int
    duration_ms: int
    position: str = "bottom"            # "top" | "bottom" | "center"
    font_size_rem: float = 1.25
    color_hex: str = "#FFFFFF"
    background_hex: Optional[str] = "#000000B3"   # rgba black 70%
    language: str = "vi"


@dataclass(frozen=True)
class TransitionSpec:
    """Chuyển cảnh giữa 2 shot."""
    transition_id: str
    kind: TransitionKind
    duration_ms: int = 500
    easing: str = "ease-in-out"

    def __post_init__(self):
        if self.duration_ms < 0:
            raise ValueError(f"Negative duration: {self.duration_ms}")


# ============================================================
# 4. TẦNG HỢP CHẤT - SCENE GRAPH (timeline DAG)
# ============================================================

@dataclass
class TimelineTrack:
    """1 track trên timeline - chứa sequence các shot/audio/caption."""
    track_id: str
    track_kind: str                     # "video" | "audio" | "caption" | "overlay"
    items: List[str] = field(default_factory=list)   # list of shot_id / audio_track_id / caption_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "track_kind": self.track_kind,
            "items": list(self.items),
        }


@dataclass
class SceneGraph:
    """
    Timeline hoàn chỉnh của 1 video/reel. Tương đương DesignGraph cho UI.
    """
    scene_id: str
    domain: MediaDomain
    canvas_resolution: Resolution
    target_duration_ms: int
    default_fps: int = 30

    shots: Dict[str, ShotSpec] = field(default_factory=dict)
    audio_tracks: Dict[str, AudioTrackSpec] = field(default_factory=dict)
    captions: Dict[str, CaptionSpec] = field(default_factory=dict)
    transitions: Dict[str, TransitionSpec] = field(default_factory=dict)
    visual_tokens: Dict[str, VisualToken] = field(default_factory=dict)

    tracks: Dict[str, TimelineTrack] = field(default_factory=dict)
    # ví dụ: {"video_main": TimelineTrack(items=[shot_A, shot_B, ...])}
    shot_transitions: Dict[Tuple[str, str], str] = field(default_factory=dict)
    # (shot_id_from, shot_id_to) -> transition_id

    metadata: Dict[str, Any] = field(default_factory=dict)

    # --------- Mutation ---------
    def add_shot(self, shot: ShotSpec) -> None:
        if shot.shot_id in self.shots:
            raise ValueError(f"Duplicate shot_id: {shot.shot_id}")
        self.shots[shot.shot_id] = shot

    def add_audio(self, track: AudioTrackSpec) -> None:
        if track.track_id in self.audio_tracks:
            raise ValueError(f"Duplicate audio track_id: {track.track_id}")
        self.audio_tracks[track.track_id] = track

    def add_caption(self, cap: CaptionSpec) -> None:
        if cap.caption_id in self.captions:
            raise ValueError(f"Duplicate caption_id: {cap.caption_id}")
        self.captions[cap.caption_id] = cap

    def add_transition(self, trans: TransitionSpec) -> None:
        if trans.transition_id in self.transitions:
            raise ValueError(f"Duplicate transition_id: {trans.transition_id}")
        self.transitions[trans.transition_id] = trans

    def add_visual_token(self, token: VisualToken) -> None:
        if token.token_id in self.visual_tokens:
            raise ValueError(f"Duplicate visual_token: {token.token_id}")
        self.visual_tokens[token.token_id] = token

    def get_or_create_track(self, track_id: str, kind: str) -> TimelineTrack:
        if track_id not in self.tracks:
            self.tracks[track_id] = TimelineTrack(track_id=track_id, track_kind=kind)
        return self.tracks[track_id]

    def append_shot_to_track(self, track_id: str, shot_id: str) -> None:
        if shot_id not in self.shots:
            raise KeyError(f"Shot not found: {shot_id}")
        track = self.get_or_create_track(track_id, "video")
        track.items.append(shot_id)

    def set_transition(
        self,
        from_shot_id: str,
        to_shot_id: str,
        transition_id: str,
    ) -> None:
        if from_shot_id not in self.shots or to_shot_id not in self.shots:
            raise KeyError("Shot ref missing")
        if transition_id not in self.transitions:
            raise KeyError(f"Transition not registered: {transition_id}")
        self.shot_transitions[(from_shot_id, to_shot_id)] = transition_id

    # --------- Query ---------
    def total_video_duration_ms(self) -> int:
        """Tổng duration của track video chính."""
        total = 0
        for track in self.tracks.values():
            if track.track_kind != "video":
                continue
            for shot_id in track.items:
                shot = self.shots.get(shot_id)
                if shot:
                    total += shot.duration_ms
        return total

    def total_audio_duration_ms(self) -> int:
        total = 0
        for track in self.audio_tracks.values():
            if track.duration_ms is not None:
                end = track.start_ms + track.duration_ms
                if end > total:
                    total = end
        return total

    # --------- Validation ---------
    def validate(self) -> List[str]:
        violations: List[str] = []

        # 1. Ít nhất 1 video track
        video_tracks = [t for t in self.tracks.values() if t.track_kind == "video"]
        if not video_tracks:
            violations.append("No video track defined")

        # 2. Mọi shot FPS đồng bộ với default_fps (cảnh báo nếu chênh)
        for sid, shot in self.shots.items():
            if shot.fps != self.default_fps:
                violations.append(
                    f"Shot {sid} fps={shot.fps} khác default_fps={self.default_fps}"
                )
            # Resolution phải fit canvas
            if (
                shot.resolution.width > self.canvas_resolution.width
                or shot.resolution.height > self.canvas_resolution.height
            ):
                violations.append(
                    f"Shot {sid} resolution {shot.resolution.width}x{shot.resolution.height} "
                    f"vượt canvas {self.canvas_resolution.width}x{self.canvas_resolution.height}"
                )

        # 3. Tổng duration video ±5% target
        total = self.total_video_duration_ms()
        if self.target_duration_ms > 0:
            drift = abs(total - self.target_duration_ms) / self.target_duration_ms
            if drift > 0.05:
                violations.append(
                    f"Total video duration {total}ms lệch {drift:.1%} vs target "
                    f"{self.target_duration_ms}ms (ngưỡng 5%)"
                )

        # 4. Visual token refs tồn tại
        for sid, shot in self.shots.items():
            if shot.visual_token_id and shot.visual_token_id not in self.visual_tokens:
                violations.append(f"Shot {sid}: visual_token '{shot.visual_token_id}' chưa đăng ký")

        # 5. Transition refs
        for (a, b), tid in self.shot_transitions.items():
            if tid not in self.transitions:
                violations.append(f"Transition {a}->{b}: ref '{tid}' không tồn tại")
            if a not in self.shots or b not in self.shots:
                violations.append(f"Transition {a}->{b}: shot ref missing")

        # 6. Caption timing nằm trong duration tổng
        for cid, cap in self.captions.items():
            end = cap.start_ms + cap.duration_ms
            if end > total + 100:   # 100ms tolerance
                violations.append(
                    f"Caption {cid} kết thúc {end}ms > video duration {total}ms"
                )

        return violations

    # --------- Serialization ---------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": ONTOLOGY_MEDIA_SCHEMA,
            "version": ONTOLOGY_MEDIA_VERSION,
            "scene_id": self.scene_id,
            "domain": self.domain.value,
            "canvas_resolution": self.canvas_resolution.to_dict(),
            "target_duration_ms": self.target_duration_ms,
            "default_fps": self.default_fps,
            "shots": {sid: asdict(s) for sid, s in self.shots.items()},
            "audio_tracks": {tid: asdict(a) for tid, a in self.audio_tracks.items()},
            "captions": {cid: asdict(c) for cid, c in self.captions.items()},
            "transitions": {tid: asdict(t) for tid, t in self.transitions.items()},
            "visual_tokens": {vid: asdict(v) for vid, v in self.visual_tokens.items()},
            "tracks": {tid: t.to_dict() for tid, t in self.tracks.items()},
            "shot_transitions": [
                {"from": a, "to": b, "transition_id": tid}
                for (a, b), tid in self.shot_transitions.items()
            ],
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()


# ============================================================
# 5. SANITY CHECK
# ============================================================

def ontology_media_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    # Build minimal scene: reel 9:16 dài 6s, 2 shots, có caption
    try:
        scene = SceneGraph(
            scene_id="scene_test",
            domain=MediaDomain.VIDEO,
            canvas_resolution=RESOLUTION_REEL_9_16,
            target_duration_ms=6000,
            default_fps=30,
        )
        scene.add_shot(ShotSpec(
            shot_id="shot_a",
            duration_ms=3000,
            fps=30,
            camera_motion=CameraMotion.STATIC,
            resolution=RESOLUTION_REEL_9_16,
        ))
        scene.add_shot(ShotSpec(
            shot_id="shot_b",
            duration_ms=3000,
            fps=30,
            camera_motion=CameraMotion.ZOOM_IN,
            resolution=RESOLUTION_REEL_9_16,
        ))
        scene.append_shot_to_track("video_main", "shot_a")
        scene.append_shot_to_track("video_main", "shot_b")
        scene.add_transition(TransitionSpec(
            transition_id="t_cross",
            kind=TransitionKind.CROSS_DISSOLVE,
            duration_ms=400,
        ))
        scene.set_transition("shot_a", "shot_b", "t_cross")
        scene.add_caption(CaptionSpec(
            caption_id="cap_1",
            text="Xin chào APEX FACTORY",
            start_ms=500,
            duration_ms=2500,
        ))
        violations = scene.validate()
        checks["scene_basic_valid"] = len(violations) == 0
        checks["scene_duration_ok"] = scene.total_video_duration_ms() == 6000
    except Exception:
        checks["scene_basic_valid"] = False
        checks["scene_error"] = False

    # Validation bắt resolution vượt canvas
    try:
        bad = SceneGraph(
            scene_id="bad",
            domain=MediaDomain.VIDEO,
            canvas_resolution=RESOLUTION_HD,
            target_duration_ms=3000,
            default_fps=30,
        )
        bad.add_shot(ShotSpec(
            shot_id="too_big",
            duration_ms=3000,
            fps=30,
            camera_motion=CameraMotion.STATIC,
            resolution=RESOLUTION_4K,      # vượt canvas HD
        ))
        bad.append_shot_to_track("video_main", "too_big")
        violations = bad.validate()
        checks["resolution_overflow_caught"] = any(
            "vượt canvas" in v for v in violations
        )
    except Exception:
        checks["resolution_overflow_caught"] = False

    # Content hash round-trip stability
    try:
        scene = SceneGraph(
            scene_id="hash_test",
            domain=MediaDomain.VIDEO,
            canvas_resolution=RESOLUTION_FHD,
            target_duration_ms=1000,
        )
        h1 = scene.content_hash()
        h2 = scene.content_hash()
        checks["hash_stable"] = h1 == h2
    except Exception:
        checks["hash_stable"] = False

    return checks


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "ONTOLOGY_MEDIA_VERSION",
    "ONTOLOGY_MEDIA_SCHEMA",
    # Enums
    "VideoCodec",
    "PixelFormat",
    "AudioCodec",
    "CameraMotion",
    "TransitionKind",
    "MediaDomain",
    # Resolution
    "Resolution",
    "RESOLUTION_HD",
    "RESOLUTION_FHD",
    "RESOLUTION_4K",
    "RESOLUTION_REEL_9_16",
    "RESOLUTION_SQUARE",
    # Atomic tokens
    "FrameToken",
    "AudioSampleToken",
    "VisualToken",
    # Molecular
    "ShotSpec",
    "AudioTrackSpec",
    "CaptionSpec",
    "TransitionSpec",
    # Compound
    "TimelineTrack",
    "SceneGraph",
    # Sanity
    "ontology_media_sanity_check",
]
