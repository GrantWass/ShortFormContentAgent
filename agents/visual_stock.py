"""Stock Footage Agent - Fetches stock video clips."""
import os
import requests
from pathlib import Path
from typing import Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class StockFootageAgent:
    """Fetches stock footage from Pexels/Pixabay."""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "visuals" / "stock"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def __call__(self, state: VideoState) -> VideoState:
        """Fetch stock footage for each prompt."""
        logger.info("🎬 [Stock Footage] Starting stock footage collection...")
        prompts = state.get("prompts", [])
        if not prompts:
            logger.error("🎬 [Stock Footage] Error: prompts are required")
            raise ValueError("prompts are required")
        
        logger.info(f"🎬 [Stock Footage] Fetching footage for {len(prompts)} prompts...")
        visual_assets = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"🎬 [Stock Footage] [{i+1}/{len(prompts)}] Searching for: {prompt[:50]}...")
            try:
                # Try Pexels first
                video_path = self._fetch_from_pexels(prompt, i)
                if not video_path:
                    # Fallback to Pixabay
                    logger.debug(f"🎬 [Stock Footage] Pexels failed, trying Pixabay...")
                    video_path = self._fetch_from_pixabay(prompt, i)
                
                if video_path:
                    visual_assets.append(str(video_path))
                    logger.info(f"🎬 [Stock Footage] ✅ Downloaded: {video_path.name}")
                else:
                    logger.warning(f"🎬 [Stock Footage] ⚠️  Could not fetch stock footage for prompt: {prompt}")
            except Exception as e:
                logger.error(f"🎬 [Stock Footage] Error fetching stock footage for prompt '{prompt}': {e}")
        
        logger.info(f"🎬 [Stock Footage] ✅ Collected {len(visual_assets)}/{len(prompts)} video clips")
        state["visual_assets"] = visual_assets
        return state
    
    def _fetch_from_pexels(self, prompt: str, index: int) -> Optional[Path]:
        """Fetch video from Pexels API using direct HTTP requests."""
        if not self.config.PEXELS_API_KEY:
            return None
        
        try:
            url = "https://api.pexels.com/videos/search"
            headers = {
                "Authorization": self.config.PEXELS_API_KEY
            }
            params = {
                "query": prompt,
                "per_page": 1,
                "orientation": "portrait"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("videos") and len(data["videos"]) > 0:
                video = data["videos"][0]
                # Get the best quality video file
                video_files = video.get("video_files", [])
                if video_files:
                    # Prefer HD quality, fallback to any available
                    hd_file = next((f for f in video_files if f.get("quality") == "hd"), None)
                    video_file = hd_file or video_files[0]
                    video_url = video_file.get("link")
                    
                    if video_url:
                        return self._download_video(video_url, f"pexels_{index}.mp4")
        except Exception as e:
            logger.debug(f"🎬 [Stock Footage] Pexels API error: {e}")
        
        return None
    
    def _fetch_from_pixabay(self, prompt: str, index: int) -> Optional[Path]:
        """Fetch video from Pixabay API."""
        if not self.config.PIXABAY_API_KEY:
            return None
        
        try:
            url = "https://pixabay.com/api/videos/"
            params = {
                "key": self.config.PIXABAY_API_KEY,
                "q": prompt,
                "video_type": "film",
                "orientation": "vertical",
                "per_page": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("hits"):
                video = data["hits"][0]
                video_url = video.get("videos", {}).get("medium", {}).get("url")
                
                if video_url:
                    return self._download_video(video_url, f"pixabay_{index}.mp4")
        except Exception as e:
            logger.debug(f"🎬 [Stock Footage] Pixabay API error: {e}")
        
        return None
    
    def _download_video(self, url: str, filename: str) -> Path:
        """Download video from URL."""
        logger.debug(f"🎬 [Stock Footage] Downloading video from URL...")
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        filepath = self.output_dir / filename
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.debug(f"🎬 [Stock Footage] Video saved to: {filepath}")
        return filepath
