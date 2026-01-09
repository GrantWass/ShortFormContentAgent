"""Caption Generator Agent - Auto-generates subtitles."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class CaptionAgent:
    """Generates captions/subtitles from script and timestamps."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def __call__(self, state: VideoState) -> VideoState:
        """Generate captions from script and timestamps."""
        logger.info("📝 [Caption Agent] Starting caption generation...")
        script = state.get("script", "")
        timestamps = state.get("timestamps", [])
        sentences = state.get("sentences", [])
        
        if not script:
            logger.error("📝 [Caption Agent] Error: script is required")
            raise ValueError("script is required")
        
        # Generate captions
        logger.debug(f"📝 [Caption Agent] Generating captions from {len(sentences)} sentences...")
        captions = self._generate_captions(script, timestamps, sentences)
        state["captions"] = captions
        logger.info(f"📝 [Caption Agent] ✅ Generated {len(captions)} caption segments")
        
        return state
    
    def _generate_captions(self, script: str, timestamps: list[dict], sentences: list[str]) -> list[dict]:
        """Generate caption objects with timing."""
        captions = []
        
        # If we have timestamps and sentences, match them up
        if timestamps and sentences:
            for i, (sentence, ts) in enumerate(zip(sentences, timestamps)):
                # Split long sentences into 2-line chunks
                words = sentence.split()
                if len(words) > 8:  # Split if more than 8 words
                    mid = len(words) // 2
                    line1 = " ".join(words[:mid])
                    line2 = " ".join(words[mid:])
                    text = f"{line1}\n{line2}"
                else:
                    text = sentence
                
                captions.append({
                    "start": ts.get("start", 0.0),
                    "end": ts.get("end", 0.0),
                    "text": text
                })
        else:
            # Fallback: create single caption
            captions.append({
                "start": 0.0,
                "end": 30.0,  # Default duration
                "text": script[:100]  # First 100 chars
            })
        
        return captions
