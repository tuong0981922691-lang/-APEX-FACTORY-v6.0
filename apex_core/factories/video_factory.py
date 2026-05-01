"""
APEX FACTORY v6.0 - Factory Layer
File: video_factory.py


Mục đích: Biến SceneGraph → sản phẩm video.
    2 chiến lược (C2 pick per brief):

    1. REMOTION (primary): sinh dự án Remotion TypeScript đầy đủ.
       - Advantage: lập trình được, chạy trên React, composable
       - Output: TS project + render script
       - Render thật qua `npx remotion render`

    2. FFMPEG_SCRIPT (fallback): sinh shell script FFmpeg cho case đơn giản.
       - Dùng khi không có Node.js hoặc muốn render nhanh
       - Concat shots + audio tracks + captions
       - Output: .sh + manifest JSON

Triết lý NT4:
    SceneGraph là ontology - không nhảy ra ngoài. Mọi shot/transition
    phải đã đăng ký trong graph trước khi emit.
"""
from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from apex_core.emitters.ast_backbone import (
    FileModule,
    FunctionDeclaration,
    ImportSpec,
    JSXAttribute,
    JSXNode,
    TSType,
)
from apex_core.emitters.react_emitter import EmitResult
from apex_core.foundation.ontology_media import (
    RESOLUTION_REEL_9_16,
    AudioTrackSpec,
    CameraMotion,
    CaptionSpec,
    MediaDomain,
    SceneGraph,
    ShotSpec,
    VideoCodec,
)
from apex_core.foundation.principles_v6 import (
    PrincipleV6,
    enforce_principle_v6,
)

# ============================================================
# 0. VERSION + CONSTANTS
# ============================================================

VIDEO_FACTORY_VERSION = "6.0.0"

REMOTION_VERSION = "^4.0.200"
REACT_VERSION_REMOTION = "^18.2.0"


# ============================================================
# 1. STRATEGY + CONFIG
# ============================================================

class VideoRenderStrategy(str, Enum):
    REMOTION = "remotion"
    FFMPEG_SCRIPT = "ffmpeg_script"


@dataclass
class VideoFactoryConfig:
    strategy: VideoRenderStrategy = VideoRenderStrategy.REMOTION
    app_name: str = "apex-factory-video"
    composition_name: str = "MainComposition"
    codec: VideoCodec = VideoCodec.H264
    quality_crf: int = 23              # FFmpeg CRF 18-28 (lower = better)
    include_captions: bool = True
    target_src_dir: str = "src"
    generate_scaffold: bool = True


# ============================================================
# 2. REMOTION EMITTER (SceneGraph → Remotion TS project)
# ============================================================

class RemotionEmitter:
    EMITTER_ID = "remotion"

    def __init__(self, config: VideoFactoryConfig):
        self.config = config

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def emit(self, scene: SceneGraph) -> EmitResult:
        warnings: List[str] = []
        violations = scene.validate()
        if violations:
            warnings.extend(violations[:5])

        files: List[FileModule] = []

        # 1. Composition.tsx (root video component)
        files.append(self._build_composition_file(scene))

        # 2. Root.tsx (register compositions with Remotion)
        files.append(self._build_root_file(scene))

        # 3. index.ts (entry)
        files.append(self._build_index_ts())

        # 4. Shot components (mỗi shot 1 file)
        for shot_id, shot in scene.shots.items():
            files.append(self._build_shot_file(shot))

        # Scaffold
        scaffold: Dict[str, str] = {}
        if self.config.generate_scaffold:
            scaffold["remotion.config.ts"] = self._render_remotion_config()
            scaffold["package.json"] = self._render_package_json()
            scaffold["tsconfig.json"] = self._render_tsconfig()
            scaffold["render.sh"] = self._render_render_script(scene)
            scaffold["scene_manifest.json"] = json.dumps(
                scene.to_dict(), indent=2, ensure_ascii=False, default=str,
            ) + "\n"

        stats = {
            "strategy": self.config.strategy.value,
            "shot_count": len(scene.shots),
            "audio_track_count": len(scene.audio_tracks),
            "caption_count": len(scene.captions),
            "transition_count": len(scene.transitions),
            "total_duration_ms": scene.total_video_duration_ms(),
            "fps": scene.default_fps,
            "canvas": f"{scene.canvas_resolution.width}x{scene.canvas_resolution.height}",
            "file_count": len(files),
            "scaffold_count": len(scaffold),
        }

        return EmitResult(
            files=files,
            entry_file_path=f"{self.config.target_src_dir}/index.ts",
            scaffold_files=scaffold,
            warnings=warnings,
            stats=stats,
        )

    # ---- Composition.tsx ----

    def _build_composition_file(self, scene: SceneGraph) -> FileModule:
        imports = [
            ImportSpec(module="react", default_name="React"),
            ImportSpec(
                module="remotion",
                named_imports=("AbsoluteFill", "Sequence", "Audio", "useCurrentFrame"),
            ),
        ]

        # Shot components
        video_track = next(
            (t for t in scene.tracks.values() if t.track_kind == "video"),
            None,
        )
        shot_ids = video_track.items if video_track else []
        for sid in shot_ids:
            comp_name = self._shot_component_name(sid)
            imports.append(ImportSpec(
                module=f"./shots/{comp_name}",
                default_name=comp_name,
            ))

        # Build JSX: AbsoluteFill > Sequences
        children: List[JSXNode] = []
        cursor_frame = 0
        for sid in shot_ids:
            shot = scene.shots.get(sid)
            if shot is None:
                continue
            duration_frames = max(1, int(round(shot.duration_ms * scene.default_fps / 1000)))
            comp_name = self._shot_component_name(sid)
            seq = JSXNode.element(
                "Sequence",
                attributes=[
                    JSXAttribute("from", str(cursor_frame), is_expression=True),
                    JSXAttribute("durationInFrames", str(duration_frames), is_expression=True),
                    JSXAttribute("name", f"Shot {sid}"),
                ],
                children=[
                    JSXNode.element(comp_name, self_closing=True),
                ],
            )
            children.append(seq)
            cursor_frame += duration_frames

        # Audio tracks
        for track_id, track in scene.audio_tracks.items():
            start_frame = max(0, int(round(track.start_ms * scene.default_fps / 1000)))
            audio_attrs = [
                JSXAttribute("src", track.source_ref),
                JSXAttribute("volume", f"{track.volume}", is_expression=True),
                JSXAttribute("startFrom", str(start_frame), is_expression=True),
            ]
            if track.duration_ms:
                end_frame = start_frame + int(round(
                    track.duration_ms * scene.default_fps / 1000
                ))
                audio_attrs.append(JSXAttribute(
                    "endAt", str(end_frame), is_expression=True,
                ))
            children.append(JSXNode.element(
                "Audio", attributes=audio_attrs, self_closing=True,
            ))

        # Captions as overlays
        if self.config.include_captions:
            for cid, cap in scene.captions.items():
                from_frame = int(round(cap.start_ms * scene.default_fps / 1000))
                dur_frames = max(1, int(round(cap.duration_ms * scene.default_fps / 1000)))
                caption_jsx = self._build_caption_jsx(cap)
                children.append(JSXNode.element(
                    "Sequence",
                    attributes=[
                        JSXAttribute("from", str(from_frame), is_expression=True),
                        JSXAttribute(
                            "durationInFrames", str(dur_frames), is_expression=True,
                        ),
                        JSXAttribute("name", f"Caption {cid}"),
                    ],
                    children=[caption_jsx],
                ))

        root_jsx = JSXNode.element(
            "AbsoluteFill",
            attributes=[
                JSXAttribute(
                    "style",
                    '{{ backgroundColor: "black" }}',
                    is_expression=True,
                ),
            ],
            children=children,
        )

        fn = FunctionDeclaration(
            name=self.config.composition_name,
            params=[],
            return_type=TSType("JSX.Element"),
            return_jsx=root_jsx,
            is_default_export=True,
            is_arrow=True,
        )

        return FileModule(
            file_path=f"{self.config.target_src_dir}/{self.config.composition_name}.tsx",
            language="typescript_react",
            imports=imports,
            top_level=[fn],
            header_comment=(
                f"Remotion composition\n"
                f"Scene: {scene.scene_id}\n"
                f"Duration: {scene.total_video_duration_ms()}ms @ {scene.default_fps}fps"
            ),
        )

    def _build_caption_jsx(self, cap: CaptionSpec) -> JSXNode:
        bg = cap.background_hex or "transparent"
        position_style = {
            "top":    "alignItems: 'flex-start', justifyContent: 'flex-start', paddingTop: 40",
            "center": "alignItems: 'center', justifyContent: 'center'",
            "bottom": "alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 80",
        }.get(cap.position, "alignItems: 'center', justifyContent: 'flex-end', paddingBottom: 80")

        outer_style = (
            f"{{{{ display: 'flex', width: '100%', height: '100%', "
            f"{position_style} }}}}"
        )
        text_style = (
            f"{{{{ color: '{cap.color_hex}', backgroundColor: '{bg}', "
            f"padding: 12, borderRadius: 8, fontSize: {cap.font_size_rem * 16}, "
            f"textAlign: 'center', maxWidth: '80%' }}}}"
        )

        # JSX text escape
        safe_text = (cap.text
                     .replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;")
                     .replace("{", "&#123;")
                     .replace("}", "&#125;"))

        return JSXNode.element(
            "div",
            attributes=[JSXAttribute("style", outer_style, is_expression=True)],
            children=[
                JSXNode.element(
                    "div",
                    attributes=[JSXAttribute("style", text_style, is_expression=True)],
                    children=[JSXNode.text_node(safe_text)],
                ),
            ],
        )

    # ---- Shot component file ----

    def _build_shot_file(self, shot: ShotSpec) -> FileModule:
        comp_name = self._shot_component_name(shot.shot_id)
        imports = [
            ImportSpec(module="react", default_name="React"),
            ImportSpec(
                module="remotion",
                named_imports=("AbsoluteFill", "useCurrentFrame", "useVideoConfig", "interpolate"),
            ),
        ]

        # Camera motion → interpolation hint in body statements
        body_stmts = [
            "const frame = useCurrentFrame();",
            "const { durationInFrames } = useVideoConfig();",
            self._camera_motion_js(shot.camera_motion),
        ]

        # JSX
        caption_style = (
            "{{ color: 'white', fontSize: 36, padding: 40, "
            "textAlign: 'center', fontFamily: 'sans-serif' }}"
        )
        root_jsx = JSXNode.element(
            "AbsoluteFill",
            attributes=[JSXAttribute(
                "style",
                "{{ backgroundColor: '#222', "
                "transform: `scale(${zoom}) translateX(${panX}px)`, "
                "display: 'flex', alignItems: 'center', justifyContent: 'center' }}",
                is_expression=True,
            )],
            children=[
                JSXNode.element(
                    "div",
                    attributes=[JSXAttribute("style", caption_style, is_expression=True)],
                    children=[JSXNode.text_node(
                        shot.subject_prompt[:200] if shot.subject_prompt else
                        f"[Shot {shot.shot_id} - {shot.camera_motion.value}]"
                    )],
                ),
            ],
        )

        fn = FunctionDeclaration(
            name=comp_name,
            params=[],
            return_type=TSType("JSX.Element"),
            body_statements=body_stmts,
            return_jsx=root_jsx,
            is_default_export=True,
            is_arrow=True,
        )

        return FileModule(
            file_path=f"{self.config.target_src_dir}/shots/{comp_name}.tsx",
            language="typescript_react",
            imports=imports,
            top_level=[fn],
            header_comment=(
                f"Shot component: {shot.shot_id}\n"
                f"Duration: {shot.duration_ms}ms, FPS: {shot.fps}, "
                f"Motion: {shot.camera_motion.value}"
            ),
        )

    @staticmethod
    def _camera_motion_js(motion: CameraMotion) -> str:
        """Return JS lines tính zoom/panX interpolation cho camera motion."""
        if motion == CameraMotion.ZOOM_IN:
            return (
                "const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.2]); "
                "const panX = 0;"
            )
        if motion == CameraMotion.ZOOM_OUT:
            return (
                "const zoom = interpolate(frame, [0, durationInFrames], [1.2, 1.0]); "
                "const panX = 0;"
            )
        if motion == CameraMotion.PAN_LEFT:
            return (
                "const zoom = 1.05; "
                "const panX = interpolate(frame, [0, durationInFrames], [0, -50]);"
            )
        if motion == CameraMotion.PAN_RIGHT:
            return (
                "const zoom = 1.05; "
                "const panX = interpolate(frame, [0, durationInFrames], [0, 50]);"
            )
        return "const zoom = 1.0; const panX = 0;"

    @staticmethod
    def _shot_component_name(shot_id: str) -> str:
        # "shot_a" → "ShotA"
        parts = shot_id.replace("-", "_").split("_")
        return "".join(p[:1].upper() + p[1:] for p in parts if p) or "Shot"

    # ---- Root.tsx (register composition) ----

    def _build_root_file(self, scene: SceneGraph) -> FileModule:
        imports = [
            ImportSpec(module="react", default_name="React"),
            ImportSpec(module="remotion", named_imports=("Composition",)),
            ImportSpec(
                module=f"./{self.config.composition_name}",
                default_name=self.config.composition_name,
            ),
        ]

        total_frames = max(
            1,
            int(round(scene.total_video_duration_ms() * scene.default_fps / 1000)),
        )

        root_jsx = JSXNode.fragment(children=[
            JSXNode.element(
                "Composition",
                attributes=[
                    JSXAttribute("id", self.config.composition_name),
                    JSXAttribute(
                        "component", self.config.composition_name, is_expression=True,
                    ),
                    JSXAttribute(
                        "durationInFrames", str(total_frames), is_expression=True,
                    ),
                    JSXAttribute("fps", str(scene.default_fps), is_expression=True),
                    JSXAttribute(
                        "width", str(scene.canvas_resolution.width),
                        is_expression=True,
                    ),
                    JSXAttribute(
                        "height", str(scene.canvas_resolution.height),
                        is_expression=True,
                    ),
                ],
                self_closing=True,
            ),
        ])

        fn = FunctionDeclaration(
            name="RemotionRoot",
            params=[],
            return_type=TSType("JSX.Element"),
            return_jsx=root_jsx,
            is_default_export=True,
            is_arrow=True,
        )

        return FileModule(
            file_path=f"{self.config.target_src_dir}/Root.tsx",
            language="typescript_react",
            imports=imports,
            top_level=[fn],
            header_comment="Remotion Root - register compositions",
        )

    def _build_index_ts(self) -> FileModule:
        content = (
            "// APEX FACTORY v6.0 - Remotion entry\n"
            "import { registerRoot } from 'remotion';\n"
            "import RemotionRoot from './Root';\n"
            "registerRoot(RemotionRoot);\n"
        )
        mod = FileModule(
            file_path=f"{self.config.target_src_dir}/index.ts",
            language="typescript",
        )
        mod.top_level.append(content)
        mod.trailing_newline = False
        return mod

    # ---- Scaffold ----

    def _render_remotion_config(self) -> str:
        return (
            "import { Config } from '@remotion/cli/config';\n"
            f"Config.setVideoImageFormat('jpeg');\n"
            f"Config.setCodec('{self.config.codec.value}');\n"
            f"Config.setCrf({self.config.quality_crf});\n"
            "Config.setConcurrency(1);\n"
            "Config.setEntryPoint('./src/index.ts');\n"
        )

    def _render_package_json(self) -> str:
        return json.dumps({
            "name": self.config.app_name,
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "start": "remotion studio",
                "build": f"remotion render {self.config.composition_name} out/video.mp4",
                "upgrade": "remotion upgrade",
            },
            "dependencies": {
                "@remotion/cli": REMOTION_VERSION,
                "remotion": REMOTION_VERSION,
                "react": REACT_VERSION_REMOTION,
                "react-dom": REACT_VERSION_REMOTION,
            },
            "devDependencies": {
                "@types/react": "^18.2.79",
                "@types/react-dom": "^18.2.25",
                "typescript": "^5.4.5",
            },
            "engines": {"node": ">=18.0.0"},
        }, indent=2) + "\n"

    def _render_tsconfig(self) -> str:
        return json.dumps({
            "compilerOptions": {
                "target": "ES2020",
                "module": "CommonJS",
                "strict": True,
                "jsx": "react-jsx",
                "esModuleInterop": True,
                "skipLibCheck": True,
                "moduleResolution": "node",
            },
            "include": [self.config.target_src_dir],
        }, indent=2) + "\n"

    def _render_render_script(self, scene: SceneGraph) -> str:
        return (
            "#!/usr/bin/env bash\n"
            "# APEX FACTORY v6.0 - Render script\n"
            "set -e\n"
            "mkdir -p out\n"
            "npm install\n"
            f"npx remotion render {self.config.composition_name} "
            f"out/{scene.scene_id}.mp4 "
            f"--codec={self.config.codec.value} "
            f"--crf={self.config.quality_crf}\n"
            "echo 'Render done: out/" + scene.scene_id + ".mp4'\n"
        )


# ============================================================
# 3. FFMPEG SCRIPT BUILDER (fallback, đơn giản)
# ============================================================

class FFmpegScriptBuilder:
    """
    Không sinh video trực tiếp, chỉ build shell script FFmpeg.
    Dùng khi không có Node.js/Remotion.

    NOTE: SceneGraph ở Factory v6 dùng shot với subject_prompt (text).
          FFmpeg không render từ text. → Builder chỉ sinh script concat
          nếu shot có `source_ref` (video file). Thiếu source → note error.
    """

    def __init__(self, config: VideoFactoryConfig):
        self.config = config

    @enforce_principle_v6(PrincipleV6.NT4_CONSTRAINED_CREATIVITY)
    def build(self, scene: SceneGraph) -> Dict[str, str]:
        """Trả dict {file_path: content}."""
        warnings: List[str] = []
        res = scene.canvas_resolution
        fps = scene.default_fps
        out_path = f"out/{scene.scene_id}.mp4"

        video_track = next(
            (t for t in scene.tracks.values() if t.track_kind == "video"),
            None,
        )
        if video_track is None or not video_track.items:
            warnings.append("No video track - ffmpeg script empty")
            return {
                "render.sh": "#!/usr/bin/env bash\n# No video track\nexit 1\n",
                "scene_manifest.json": json.dumps(
                    scene.to_dict(), indent=2, ensure_ascii=False, default=str,
                ),
                "BUILD_WARNINGS.txt": "\n".join(warnings),
            }

        lines = [
            "#!/usr/bin/env bash",
            "# APEX FACTORY v6.0 - FFmpeg render script",
            "set -e",
            "mkdir -p out",
            "",
        ]

        # Build concat list file
        concat_path = f"out/concat_{scene.scene_id}.txt"
        concat_entries: List[str] = []

        for idx, shot_id in enumerate(video_track.items):
            shot = scene.shots.get(shot_id)
            if shot is None:
                continue
            src = (shot.metadata or {}).get("source_ref")
            if not src:
                warnings.append(
                    f"Shot {shot_id} không có metadata.source_ref - skip "
                    f"(FFmpeg cần file video)"
                )
                continue
            # Add ffconcat directive with duration
            duration_sec = shot.duration_ms / 1000.0
            concat_entries.append(f"file {shlex.quote(src)}")
            concat_entries.append(f"duration {duration_sec}")

        if not concat_entries:
            return {
                "render.sh": "#!/usr/bin/env bash\n# No valid shots\nexit 1\n",
                "BUILD_WARNINGS.txt": "\n".join(warnings),
            }

        concat_content = "ffconcat version 1.0\n" + "\n".join(concat_entries) + "\n"

        # Audio input
        audio_inputs: List[str] = []
        for track in scene.audio_tracks.values():
            if track.source_ref:
                audio_inputs.append(f'-i {shlex.quote(track.source_ref)}')

        audio_flags = (
            " ".join(audio_inputs)
            if audio_inputs else ""
        )
        audio_mix = ""
        if len(audio_inputs) >= 1:
            # Giả định: 1 track voiceover + 1 music (đơn giản)
            if len(audio_inputs) == 1:
                audio_mix = "-map 1:a"
            else:
                # amix filter
                inputs_str = "".join(f"[{i+1}:a]" for i in range(len(audio_inputs)))
                audio_mix = (
                    f'-filter_complex "{inputs_str}amix=inputs={len(audio_inputs)}'
                    f':duration=longest[aout]" -map "[aout]"'
                )

        # Captions via drawtext (đơn giản, 1 caption chính)
        video_filters = (
            f"scale={res.width}:{res.height},fps={fps}"
        )

        cmd = (
            f"ffmpeg -y -f concat -safe 0 -i {shlex.quote(concat_path)} "
            f"{audio_flags} "
            f'-vf "{video_filters}" '
            f"{audio_mix} "
            f"-c:v lib{self.config.codec.value} "
            f"-crf {self.config.quality_crf} "
            f"-c:a aac -b:a 192k "
            f"-movflags +faststart "
            f"{shlex.quote(out_path)}"
        )

        lines.append(f"cat > {shlex.quote(concat_path)} << 'EOF'")
        lines.append(concat_content.rstrip())
        lines.append("EOF")
        lines.append("")
        lines.append(cmd)
        lines.append(f"echo 'Rendered: {out_path}'")

        output_files = {
            "render.sh": "\n".join(lines) + "\n",
            "scene_manifest.json": json.dumps(
                scene.to_dict(), indent=2, ensure_ascii=False, default=str,
            ) + "\n",
        }
        if warnings:
            output_files["BUILD_WARNINGS.txt"] = "\n".join(warnings) + "\n"
        return output_files


# ============================================================
# 4. VIDEO FACTORY FACADE
# ============================================================

class VideoFactory:
    def __init__(self, config: Optional[VideoFactoryConfig] = None):
        self.config = config or VideoFactoryConfig()

    @enforce_principle_v6(PrincipleV6.NT5_HUMAN_SUPREMACY)
    def build_from_scene(self, scene: SceneGraph) -> EmitResult:
        if self.config.strategy == VideoRenderStrategy.REMOTION:
            return RemotionEmitter(self.config).emit(scene)
        elif self.config.strategy == VideoRenderStrategy.FFMPEG_SCRIPT:
            scaffold = FFmpegScriptBuilder(self.config).build(scene)
            return EmitResult(
                files=[],
                entry_file_path="render.sh",
                scaffold_files=scaffold,
                warnings=[],
                stats={
                    "strategy": "ffmpeg_script",
                    "shot_count": len(scene.shots),
                },
            )
        raise ValueError(f"Unknown strategy {self.config.strategy}")


# ============================================================
# 5. SANITY CHECK
# ============================================================

def video_factory_sanity_check() -> Dict[str, bool]:
    checks: Dict[str, bool] = {}

    scene = SceneGraph(
        scene_id="reel_01",
        domain=MediaDomain.VIDEO,
        canvas_resolution=RESOLUTION_REEL_9_16,
        target_duration_ms=6000,
        default_fps=30,
    )
    scene.add_shot(ShotSpec(
        shot_id="shot_a", duration_ms=3000, fps=30,
        camera_motion=CameraMotion.ZOOM_IN,
        resolution=RESOLUTION_REEL_9_16,
        subject_prompt="Cafe morning vibes",
    ))
    scene.add_shot(ShotSpec(
        shot_id="shot_b", duration_ms=3000, fps=30,
        camera_motion=CameraMotion.PAN_RIGHT,
        resolution=RESOLUTION_REEL_9_16,
        subject_prompt="Latte art closeup",
    ))
    scene.append_shot_to_track("video_main", "shot_a")
    scene.append_shot_to_track("video_main", "shot_b")
    scene.add_caption(CaptionSpec(
        caption_id="cap1", text="APEX Factory",
        start_ms=500, duration_ms=2500,
    ))
    scene.add_audio(AudioTrackSpec(
        track_id="bgm", kind="music", source_ref="./music.mp3",
        start_ms=0, duration_ms=6000, volume=0.6,
    ))

    # Remotion
    factory = VideoFactory(VideoFactoryConfig(
        strategy=VideoRenderStrategy.REMOTION,
    ))
    result = factory.build_from_scene(scene)
    checks["remotion_result"] = isinstance(result, EmitResult)
    checks["has_composition_file"] = any(
        f.file_path.endswith(f"{VideoFactoryConfig().composition_name}.tsx")
        for f in result.files
    )
    checks["has_root_file"] = any(
        f.file_path.endswith("Root.tsx") for f in result.files
    )
    checks["has_shot_files"] = sum(
        1 for f in result.files if "/shots/" in f.file_path
    ) == 2
    checks["has_package_json"] = "package.json" in result.scaffold_files
    checks["has_render_sh"] = "render.sh" in result.scaffold_files

    # Composition content check
    comp_file = next(
        f for f in result.files
        if f.file_path.endswith(f"{VideoFactoryConfig().composition_name}.tsx")
    )
    rendered = comp_file.render()
    checks["composition_has_sequence"] = "<Sequence" in rendered
    checks["composition_has_audio"] = "<Audio" in rendered

    # FFmpeg strategy
    factory2 = VideoFactory(VideoFactoryConfig(
        strategy=VideoRenderStrategy.FFMPEG_SCRIPT,
    ))
    result2 = factory2.build_from_scene(scene)
    # Không có source_ref trong shot.metadata → warn but script sinh
    checks["ffmpeg_has_manifest"] = "scene_manifest.json" in result2.scaffold_files
    checks["ffmpeg_has_warnings"] = "BUILD_WARNINGS.txt" in result2.scaffold_files

    return checks


__all__ = [
    "VIDEO_FACTORY_VERSION",
    "REMOTION_VERSION",
    "VideoRenderStrategy", "VideoFactoryConfig",
    "RemotionEmitter", "FFmpegScriptBuilder",
    "VideoFactory",
    "video_factory_sanity_check",
]

