import io
import logging
from typing import Optional, Dict, Any

from openai import AsyncOpenAI
from core.config import settings
from schemas.transcription import TranscriptionResult
from .base import TranscriptionProvider

logger = logging.getLogger(__name__)

class GroqWhisperProvider(TranscriptionProvider):
    """Transcription provider using Groq's Whisper API."""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be set in environment variables")
            
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = "whisper-large-v3"
        logger.info(f"Initialized GroqWhisperProvider with model {self.model}")

    async def transcribe(self, audio_bytes: bytes, prompt: Optional[str] = None) -> Optional[TranscriptionResult]:
        if len(audio_bytes) < 100:
            return None
            
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        
        # Truncate prompt if provided (Groq might have limits)
        safe_prompt = prompt[:448] if prompt else None
        
        try:
            kwargs = {
                "model": self.model,
                "file": audio_file,
                "response_format": "verbose_json",
                "language": "en",
                "temperature": 0,
            }
            if safe_prompt:
                kwargs["prompt"] = safe_prompt
                
            response = await self.client.audio.transcriptions.create(**kwargs)
            
            # Extract fields from verbose_json response
            text = response.text.strip() if hasattr(response, 'text') else ""
            language = getattr(response, 'language', 'en')
            duration = getattr(response, 'duration', 0.0)
            
            if not text:
                return None
                
            return TranscriptionResult(
                text=text,
                language=language,
                duration_seconds=duration,
                provider="groq"
            )
        except Exception as e:
            logger.error(f"Groq transcription error: {e}", extra={"operation": "transcribe_groq"})
            return None

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "groq",
            "model": self.model,
            "configured": bool(self.api_key)
        }
