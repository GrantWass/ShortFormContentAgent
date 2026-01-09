"""AI Video Agent - Generates video clips using AI services."""
from pathlib import Path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class AIVideoAgent:
    """Generates video clips using Runway/Pika/Kling/Luma APIs."""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "visuals" / "ai_video"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def __call__(self, state: VideoState) -> VideoState:
        """Generate AI video clips for each prompt."""
        logger.info("🤖 [AI Video] Starting AI video generation...")
        prompts = state.get("prompts", [])
        if not prompts:
            logger.error("🤖 [AI Video] Error: prompts are required")
            raise ValueError("prompts are required")
        
        logger.info(f"🤖 [AI Video] Generating videos for {len(prompts)} prompts...")
        visual_assets = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"🤖 [AI Video] [{i+1}/{len(prompts)}] Generating: {prompt[:50]}...")
            try:
                # Try Pika first (fastest), then Kling (best quality), then Runway, then Luma
                video_path = None
                
                if self.config.PIKA_API_KEY:
                    logger.debug("🤖 [AI Video] Trying Pika API (fastest)...")
                    video_path = self._generate_pika(prompt, i)
                
                if not video_path and self.config.KLING_API_KEY:
                    logger.debug("🤖 [AI Video] Trying Kling API (best quality)...")
                    video_path = self._generate_kling(prompt, i)
                
                if not video_path and self.config.RUNWAY_API_KEY:
                    logger.debug("🤖 [AI Video] Trying Runway API...")
                    video_path = self._generate_runway(prompt, i)
                
                if not video_path and self.config.LUMA_API_KEY:
                    logger.debug("🤖 [AI Video] Trying Luma API...")
                    video_path = self._generate_luma(prompt, i)
                
                if video_path:
                    visual_assets.append(str(video_path))
                    logger.info(f"🤖 [AI Video] ✅ Generated: {video_path.name}")
                else:
                    logger.warning(f"🤖 [AI Video] ⚠️  No AI video API keys configured, creating placeholder for: {prompt}")
                    # Create placeholder
                    video_path = self._create_placeholder(prompt, i)
                    if video_path:
                        visual_assets.append(str(video_path))
                        logger.info(f"🤖 [AI Video] ✅ Created placeholder: {video_path.name}")
            except Exception as e:
                logger.error(f"🤖 [AI Video] Error generating AI video for prompt '{prompt}': {e}")
        
        logger.info(f"🤖 [AI Video] ✅ Generated {len(visual_assets)}/{len(prompts)} video assets")
        state["visual_assets"] = visual_assets
        return state
    
    def _generate_runway(self, prompt: str, index: int) -> Path | None:
        """Generate video using Runway API."""
        # Placeholder - Runway API integration
        # Actual implementation depends on Runway's API structure
        logger.debug(f"🤖 [AI Video] Runway generation not yet implemented for: {prompt}")
        return None
    
    def _generate_pika(self, prompt: str, index: int) -> Path | None:
        """Generate video using Pika API."""
        # Placeholder - Pika API integration
        logger.debug(f"🤖 [AI Video] Pika generation not yet implemented for: {prompt}")
        return None
    
    def _generate_kling(self, prompt: str, index: int) -> Path | None:
        """Generate video using Kling API."""
        # Placeholder - Kling API integration
        # Kling AI is excellent for TikTok content with Hollywood-quality motion
        logger.debug(f"🤖 [AI Video] Kling generation not yet implemented for: {prompt}")
        return None
    
    def _generate_luma(self, prompt: str, index: int) -> Path | None:
        """Generate video using Luma API."""
        # Placeholder - Luma API integration
        logger.debug(f"🤖 [AI Video] Luma generation not yet implemented for: {prompt}")
        return None
    
    def _create_placeholder(self, prompt: str, index: int) -> Path:
        """Create a placeholder image/video when AI generation is unavailable."""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple placeholder image
        img = Image.new("RGB", (1080, 1920), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        except:
            font = ImageFont.load_default()
        
        # Draw prompt text (wrapped)
        text = prompt[:100]  # Truncate long prompts
        draw.text((540, 960), text, fill=(255, 255, 255), font=font, anchor="mm")
        
        filepath = self.output_dir / f"placeholder_{index}.png"
        img.save(filepath)
        return filepath
