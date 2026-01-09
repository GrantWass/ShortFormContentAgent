"""Voiceover Agent - Converts script to speech."""
from pathlib import Path
from openai import OpenAI
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from state import VideoState
from config import Config
from logger import logger


class VoiceoverAgent:
    """Generates voiceover audio from script."""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
    
    def __call__(self, state: VideoState) -> VideoState:
        """Generate voiceover from script."""
        logger.info("🎤 [Voiceover] Starting voiceover generation...")
        script = state.get("script", "")
        if not script:
            logger.error("🎤 [Voiceover] Error: script is required")
            raise ValueError("script is required")
        
        logger.info(f"🎤 [Voiceover] Script length: {len(script)} characters")
        
        # Try ElevenLabs first (better quality), fallback to OpenAI TTS
        voiceover_path = None
        
        if self.config.ELEVENLABS_API_KEY:
            logger.info("🎤 [Voiceover] Attempting ElevenLabs generation...")
            voiceover_path = self._generate_elevenlabs(script)
        
        if not voiceover_path and self.openai_client:
            logger.info("🎤 [Voiceover] Attempting OpenAI TTS generation...")
            voiceover_path = self._generate_openai_tts(script)
        
        if not voiceover_path:
            logger.error("🎤 [Voiceover] No voiceover service available")
            raise ValueError("No voiceover service available. Configure ELEVENLABS_API_KEY or OPENAI_API_KEY")
        
        state["voiceover_path"] = str(voiceover_path)
        logger.info(f"🎤 [Voiceover] ✅ Voiceover saved to: {voiceover_path}")
        
        # Generate timestamps (simple estimation based on word count)
        logger.debug("🎤 [Voiceover] Generating timestamps...")
        state["timestamps"] = self._estimate_timestamps(script)
        logger.info(f"🎤 [Voiceover] ✅ Generated {len(state['timestamps'])} timestamp segments")
        
        return state
    
    def _generate_elevenlabs(self, script: str) -> Path | None:
        """Generate voiceover using ElevenLabs."""
        try:
            from elevenlabs import generate, save
            
            audio = generate(
                text=script,
                voice="Rachel",  # Default voice, can be configured
                model="eleven_multilingual_v2"
            )
            
            filepath = self.output_dir / "voiceover.mp3"
            save(audio, str(filepath))
            return filepath
        except Exception as e:
            logger.warning(f"🎤 [Voiceover] ElevenLabs generation error: {e}")
            return None
    
    def _generate_openai_tts(self, script: str) -> Path | None:
        """Generate voiceover using OpenAI TTS."""
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=script,
                speed=1.0  # Adjust for ~150 WPM pacing
            )
            
            filepath = self.output_dir / "voiceover.mp3"
            response.stream_to_file(str(filepath))
            return filepath
        except Exception as e:
            logger.warning(f"🎤 [Voiceover] OpenAI TTS generation error: {e}")
            return None
    
    def _estimate_timestamps(self, script: str) -> list[dict[str, float]]:
        """Estimate timestamps for each sentence."""
        sentences = script.split(". ")
        timestamps = []
        current_time = 0.0
        
        # Rough estimate: 150 words per minute = 2.5 words per second
        words_per_second = 2.5
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            word_count = len(sentence.split())
            duration = word_count / words_per_second
            
            timestamps.append({
                "start": current_time,
                "end": current_time + duration
            })
            
            current_time += duration
        
        return timestamps
