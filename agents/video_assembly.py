"""Video Assembly Agent - Assembles final TikTok video."""
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class VideoAssemblyAgent:
    """Assembles visuals, voiceover, and captions into final video."""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def __call__(self, state: VideoState) -> VideoState:
        """Assemble final video."""
        logger.info("🎬 [Video Assembly] Starting video assembly...")
        visual_assets = state.get("visual_assets", [])
        voiceover_path = state.get("voiceover_path", "")
        captions = state.get("captions", [])
        
        if not visual_assets:
            logger.error("🎬 [Video Assembly] Error: visual_assets are required")
            raise ValueError("visual_assets are required")
        if not voiceover_path:
            logger.error("🎬 [Video Assembly] Error: voiceover_path is required")
            raise ValueError("voiceover_path is required")
        
        logger.info(f"🎬 [Video Assembly] Assembling video with {len(visual_assets)} visual assets")
        logger.info(f"🎬 [Video Assembly] Voiceover: {voiceover_path}")
        logger.info(f"🎬 [Video Assembly] Captions: {len(captions)} segments")
        
        # Assemble video using FFmpeg
        logger.info("🎬 [Video Assembly] Processing and combining assets...")
        final_video_path = self._assemble_video(visual_assets, voiceover_path, captions)
        
        state["final_video_path"] = str(final_video_path)
        logger.info(f"🎬 [Video Assembly] ✅ Final video saved to: {final_video_path}")
        return state
    
    def _assemble_video(self, visual_assets: list[str], voiceover_path: str, captions: list[dict]) -> Path:
        """Assemble video using FFmpeg."""
        try:
            import ffmpeg
            logger.debug("🎬 [Video Assembly] Using FFmpeg for assembly")
        except ImportError:
            logger.info("🎬 [Video Assembly] FFmpeg not available, using MoviePy fallback")
            # Fallback to moviepy
            return self._assemble_with_moviepy(visual_assets, voiceover_path, captions)
        
        # Use FFmpeg for assembly
        output_path = self.output_dir / "final_video.mp4"
        
        # This is a simplified version - full implementation would:
        # 1. Process each visual asset (resize, trim, etc.)
        # 2. Concatenate visuals
        # 3. Overlay voiceover
        # 4. Add captions as burn-in subtitles
        # 5. Add background music
        # 6. Export as 1080x1920 MP4
        
        # For now, create a basic concatenation
        # Full implementation would require more complex FFmpeg commands
        
        return self._assemble_with_moviepy(visual_assets, voiceover_path, captions)
    
    def _assemble_with_moviepy(self, visual_assets: list[str], voiceover_path: str, captions: list[dict]) -> Path:
        """Assemble video using MoviePy (fallback)."""
        from moviepy.editor import (
            VideoFileClip, ImageClip, AudioFileClip,
            concatenate_videoclips, CompositeVideoClip, TextClip
        )
        from moviepy.video.fx import resize
        
        output_path = self.output_dir / "final_video.mp4"
        
        clips = []
        
        # Process each visual asset
        logger.debug(f"🎬 [Video Assembly] Processing {len(visual_assets)} visual assets...")
        for i, asset_path in enumerate(visual_assets):
            path = Path(asset_path)
            if not path.exists():
                logger.warning(f"🎬 [Video Assembly] Visual asset not found: {asset_path}")
                continue
            logger.debug(f"🎬 [Video Assembly] [{i+1}/{len(visual_assets)}] Processing: {path.name}")
            
            if path.suffix.lower() in [".mp4", ".mov", ".avi"]:
                # Video clip
                clip = VideoFileClip(str(path))
            else:
                # Image - create clip with duration
                clip = ImageClip(str(path))
                # Set duration based on corresponding caption or default
                clip = clip.set_duration(3.0)  # Default 3 seconds
            
            # Resize to vertical format
            clip = clip.resize(height=self.config.VIDEO_HEIGHT)
            # Center crop if needed
            if clip.w > self.config.VIDEO_WIDTH:
                clip = clip.crop(x_center=clip.w/2, width=self.config.VIDEO_WIDTH)
            
            clips.append(clip)
        
        if not clips:
            logger.error("🎬 [Video Assembly] No valid visual assets found")
            raise ValueError("No valid visual assets found")
        
        logger.info(f"🎬 [Video Assembly] Concatenating {len(clips)} clips...")
        # Concatenate clips
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Add voiceover
        logger.info("🎬 [Video Assembly] Adding voiceover audio...")
        audio = AudioFileClip(str(voiceover_path))
        final_clip = final_clip.set_audio(audio)
        
        # Trim to audio length
        if final_clip.duration > audio.duration:
            logger.debug(f"🎬 [Video Assembly] Trimming video to audio length: {audio.duration:.2f}s")
            final_clip = final_clip.subclip(0, audio.duration)
        
        # Add captions (simplified - would need proper timing)
        # For full implementation, use TextClip with timing from captions list
        logger.debug("🎬 [Video Assembly] Caption overlay not yet implemented")
        
        # Export
        logger.info(f"🎬 [Video Assembly] Exporting final video to: {output_path}")
        logger.info("🎬 [Video Assembly] This may take a while...")
        final_clip.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium"
        )
        logger.info(f"🎬 [Video Assembly] Video duration: {final_clip.duration:.2f} seconds")
        
        # Cleanup
        final_clip.close()
        audio.close()
        for clip in clips:
            clip.close()
        
        return output_path
