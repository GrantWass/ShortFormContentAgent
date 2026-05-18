"""Configuration management for the TikTok generator."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration for API keys and settings."""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    PEXELS_API_KEY: Optional[str] = os.getenv("PEXELS_API_KEY")
    PIXABAY_API_KEY: Optional[str] = os.getenv("PIXABAY_API_KEY")
    RUNWAY_API_KEY: Optional[str] = os.getenv("RUNWAY_API_KEY")
    PIKA_API_KEY: Optional[str] = os.getenv("PIKA_API_KEY")
    KLING_API_KEY: Optional[str] = os.getenv("KLING_API_KEY")
    LUMA_API_KEY: Optional[str] = os.getenv("LUMA_API_KEY")
    NYT_API_KEY: Optional[str] = os.getenv("NYT_API_KEY")
    
    # Paths
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./outputs"))
    
    # Short-form video settings
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    TARGET_DURATION_SECONDS: tuple[int, int] = (30, 60)
    WORDS_PER_MINUTE: int = 150

    # YouTube long-form settings
    YOUTUBE_WIDTH: int = 1920
    YOUTUBE_HEIGHT: int = 1080
    YOUTUBE_TARGET_WORDS: tuple[int, int] = (1800, 2000)  # ~12 min at 150 WPM
    YOUTUBE_TITLE_CARD_DURATION: int = 3  # seconds per chapter title card
    YOUTUBE_CLIP_DURATION: int = 7  # default seconds per Ken Burns image clip
    
    # Visual Strategy Settings
    STOCK_FOOTAGE_DURATION: tuple[int, int] = (3, 5)  # seconds per clip
    AI_VIDEO_DURATION: tuple[int, int] = (3, 5)
    
    # Audio Settings
    BACKGROUND_MUSIC_VOLUME_DB: float = -20.0
    
    # LLM Settings
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    TEMPERATURE: float = 0.7
    
    def __init__(self):
        """Initialize output directory."""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> list[str]:
        """Validate required API keys are present."""
        errors = []
        if not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        return errors
