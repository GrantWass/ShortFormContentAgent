"""YouTube Video Assembly Agent - Assembles 1920x1080 long-form videos."""
import subprocess
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class YouTubeVideoAssemblyAgent:
    """Assembles YouTube long-form video: Ken Burns images + chapter cards + voiceover."""

    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "videos"
        self.clips_dir = config.OUTPUT_DIR / "visuals" / "yt_clips"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.W = config.YOUTUBE_WIDTH
        self.H = config.YOUTUBE_HEIGHT

    def __call__(self, state: VideoState) -> VideoState:
        logger.info("🎞️  [YT Assembly] Starting YouTube video assembly...")
        visual_assets = state.get("visual_assets", [])
        voiceover_path = state.get("voiceover_path", "")
        chapters = state.get("chapters", [])
        timestamps = state.get("timestamps", [])

        if not voiceover_path:
            raise ValueError("voiceover_path is required")

        output_path = self._assemble(visual_assets, voiceover_path, chapters, timestamps)
        state["final_video_path"] = str(output_path)
        logger.info(f"🎞️  [YT Assembly] ✅ Final video: {output_path}")
        return state

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def _assemble(self, visual_assets, voiceover_path, chapters, timestamps):
        """Build the clip schedule, render each clip, then concatenate."""
        schedule = self._build_schedule(visual_assets, chapters, timestamps)
        logger.info(f"🎞️  [YT Assembly] Rendering {len(schedule)} clips...")

        clip_paths = []
        for i, (asset, duration, label) in enumerate(schedule):
            logger.info(f"🎞️  [YT Assembly] [{i+1}/{len(schedule)}] {label} ({duration:.1f}s)")
            if label.startswith("TITLE:"):
                path = self._render_title_card(label[6:], duration, i)
            else:
                path = self._render_ken_burns(asset, duration, i)
            if path:
                clip_paths.append(path)

        if not clip_paths:
            raise ValueError("No clips rendered — cannot assemble video")

        output_path = self.output_dir / "youtube_video.mp4"
        self._ffmpeg_concat(clip_paths, voiceover_path, output_path)
        return output_path

    # ------------------------------------------------------------------
    # Schedule builder
    # ------------------------------------------------------------------

    def _build_schedule(self, visual_assets, chapters, timestamps) -> list[tuple]:
        """Return [(asset_path_or_None, duration_secs, label), ...]."""
        schedule = []
        asset_idx = 0
        sentence_idx = 0

        if chapters and timestamps:
            for chapter in chapters:
                title = chapter.get("title", "Section")
                queries = chapter.get("image_queries", [])
                sentences = chapter.get("sentences", [])

                # Chapter title card
                schedule.append((None, self.config.YOUTUBE_TITLE_CARD_DURATION, f"TITLE:{title}"))

                if not queries:
                    continue

                sentences_per_img = max(1, len(sentences) // len(queries))

                for q_idx in range(len(queries)):
                    asset = visual_assets[asset_idx] if asset_idx < len(visual_assets) else None
                    asset_idx += 1

                    # Determine duration from timestamps for the covered sentences
                    s_start = sentence_idx
                    s_end = min(sentence_idx + sentences_per_img, len(timestamps))
                    if s_start < len(timestamps) and s_end > s_start:
                        duration = max(
                            3.0,
                            timestamps[s_end - 1]["end"] - timestamps[s_start]["start"],
                        )
                        sentence_idx = s_end
                    else:
                        duration = float(self.config.YOUTUBE_CLIP_DURATION)

                    schedule.append((asset, duration, f"img_c{len(schedule)}"))
        else:
            # Fallback: evenly spread all images
            n = max(1, len(visual_assets))
            dur = self.config.YOUTUBE_CLIP_DURATION
            for asset in visual_assets:
                schedule.append((asset, float(dur), "img"))

        return schedule

    # ------------------------------------------------------------------
    # Clip renderers
    # ------------------------------------------------------------------

    def _render_ken_burns(self, img_path, duration: float, idx: int) -> Path | None:
        """Render a Ken Burns zoom-pan clip from an image using FFmpeg."""
        out = self.clips_dir / f"clip_{idx:04d}_kb.mp4"

        if not img_path or not Path(img_path).exists():
            return self._render_color_card(duration, idx, color="0x141414")

        fps = 30
        n_frames = int(duration * fps)
        # zoompan: slow zoom-in while panning slightly right
        vf = (
            f"zoompan="
            f"z='min(zoom+0.0008,1.3)':"
            f"x='iw/2-(iw/zoom/2)+iw*0.03*on/{n_frames}':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={n_frames}:"
            f"s={self.W}x{self.H}:"
            f"fps={fps},"
            f"scale={self.W}:{self.H},"
            f"setsar=1"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-vf", vf,
            "-t", str(duration),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast",
            str(out),
        ]
        if self._run(cmd, f"Ken Burns clip {idx}"):
            return out
        # Fallback to plain image clip if FFmpeg fails
        return self._render_plain_image(img_path, duration, idx)

    def _render_plain_image(self, img_path, duration: float, idx: int) -> Path | None:
        """Render a static image clip (no Ken Burns) as FFmpeg fallback."""
        out = self.clips_dir / f"clip_{idx:04d}_plain.mp4"
        vf = f"scale={self.W}:{self.H}:force_original_aspect_ratio=decrease,pad={self.W}:{self.H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-vf", vf,
            "-t", str(duration),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast",
            str(out),
        ]
        if self._run(cmd, f"plain image clip {idx}"):
            return out
        return None

    def _render_title_card(self, title: str, duration: float, idx: int) -> Path | None:
        """Render a chapter title card image and convert to a short video clip."""
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont

        # Build the title card image
        img = Image.new("RGB", (self.W, self.H), color=(15, 15, 15))
        draw = ImageDraw.Draw(img)

        # Red accent bar on the left
        bar_x = 120
        draw.rectangle([bar_x, self.H // 2 - 70, bar_x + 8, self.H // 2 + 70], fill=(220, 50, 50))

        # Load font (fall back gracefully)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        font = ImageFont.load_default()
        for fp in font_paths:
            if Path(fp).exists():
                try:
                    font = ImageFont.truetype(fp, 72)
                    break
                except Exception:
                    pass

        # Word-wrap title to fit within margins
        margin_x = bar_x + 40
        max_w = self.W - margin_x - 80
        lines = self._wrap_text(draw, title, font, max_w)
        line_h = 90
        total_h = len(lines) * line_h
        y = (self.H - total_h) // 2

        for line in lines:
            draw.text((margin_x, y), line, font=font, fill=(255, 255, 255))
            y += line_h

        # Save image then encode to video with FFmpeg
        img_path = self.clips_dir / f"card_{idx:04d}.png"
        img.save(str(img_path))

        out = self.clips_dir / f"clip_{idx:04d}_card.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path),
            "-t", str(duration),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast",
            str(out),
        ]
        if self._run(cmd, f"title card {idx}"):
            return out
        return None

    def _render_color_card(self, duration: float, idx: int, color: str = "0x141414") -> Path | None:
        """Render a solid-color fallback clip."""
        out = self.clips_dir / f"clip_{idx:04d}_color.mp4"
        vf = f"color=c={color}:s={self.W}x{self.H}:r=30"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", vf,
            "-t", str(duration),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(out),
        ]
        if self._run(cmd, f"color card {idx}"):
            return out
        return None

    # ------------------------------------------------------------------
    # Final concatenation
    # ------------------------------------------------------------------

    def _ffmpeg_concat(self, clip_paths: list[Path], voiceover_path: str, output_path: Path):
        """Concatenate all clips, add voiceover, write final MP4."""
        concat_file = self.clips_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for p in clip_paths:
                f.write(f"file '{p.resolve()}'\n")

        logger.info(f"🎞️  [YT Assembly] Concatenating {len(clip_paths)} clips + audio...")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-i", str(voiceover_path),
            "-c:v", "libx264", "-c:a", "aac",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        if not self._run(cmd, "final concat"):
            raise RuntimeError("FFmpeg final concatenation failed — check logs")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run(self, cmd: list, label: str) -> bool:
        """Run an FFmpeg command; return True on success."""
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"🎞️  [YT Assembly] FFmpeg {label} failed:\n{result.stderr[-500:]}")
            return False
        return True

    def _wrap_text(self, draw, text: str, font, max_width: int) -> list[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            test = " ".join(current + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines or [text]
