"""Image Slideshow Agent - Generates images and prepares for slideshow."""
from pathlib import Path
from openai import OpenAI
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class ImageSlideshowAgent:
    """Generates images using DALL·E or similar, prepares for slideshow animation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "visuals" / "slideshow"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
    
    def __call__(self, state: VideoState) -> VideoState:
        """Generate images for each prompt."""
        logger.info("🖼️  [Image Slideshow] Starting image generation...")
        prompts = state.get("prompts", [])
        if not prompts:
            logger.error("🖼️  [Image Slideshow] Error: prompts are required")
            raise ValueError("prompts are required")
        
        logger.info(f"🖼️  [Image Slideshow] Generating images for {len(prompts)} prompts...")
        visual_assets = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"🖼️  [Image Slideshow] [{i+1}/{len(prompts)}] Generating: {prompt[:50]}...")
            try:
                image_path = self._generate_image(prompt, i)
                if image_path:
                    visual_assets.append(str(image_path))
                    logger.info(f"🖼️  [Image Slideshow] ✅ Generated: {image_path.name}")
            except Exception as e:
                logger.error(f"🖼️  [Image Slideshow] Error generating image for prompt '{prompt}': {e}")
        
        logger.info(f"🖼️  [Image Slideshow] ✅ Generated {len(visual_assets)}/{len(prompts)} images")
        state["visual_assets"] = visual_assets
        return state
    
    def _generate_image(self, prompt: str, index: int) -> Path | None:
        """Generate image using DALL·E."""
        if not self.client:
            logger.warning("🖼️  [Image Slideshow] OpenAI client not available for image generation")
            return None
        
        try:
            # Generate image with vertical aspect ratio
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=f"{prompt}, vertical format, 9:16 aspect ratio, cinematic, no text, no logos",
                size="1024x1792",  # Vertical format
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download image
            import requests
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            filepath = self.output_dir / f"image_{index}.png"
            with open(filepath, "wb") as f:
                f.write(img_response.content)
            
            return filepath
        except Exception as e:
            logger.warning(f"🖼️  [Image Slideshow] DALL·E generation error: {e}, creating placeholder")
            # Fallback: create placeholder
            return self._create_placeholder(prompt, index)
    
    def _create_placeholder(self, prompt: str, index: int) -> Path:
        """Create a placeholder image."""
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new("RGB", (1024, 1792), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
        except:
            font = ImageFont.load_default()
        
        text = prompt[:100]
        draw.text((512, 896), text, fill=(255, 255, 255), font=font, anchor="mm")
        
        filepath = self.output_dir / f"placeholder_{index}.png"
        img.save(filepath)
        return filepath
