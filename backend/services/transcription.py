import io
import logging
from datetime import datetime

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Handles audio transcription using Whisper API.

    Each call to transcribe() expects a complete, self-contained audio file
    (e.g., a full WebM with headers). The frontend is responsible for sending
    complete audio chunks by stopping/restarting the MediaRecorder per interval.
    """

    def __init__(self, api_key: str, api_url: str, model: str | None = None):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_url,
        )

        # Auto-detect model based on API URL
        if model:
            self._model = model
        elif "groq.com" in api_url:
            self._model = "whisper-large-v3-turbo"
        else:
            self._model = "whisper-1"

        logger.info(f"Transcription service initialized: url={api_url}, model={self._model}")

    async def transcribe(self, audio_data: bytes) -> dict | None:
        """Transcribe a complete audio file using Whisper API.

        Args:
            audio_data: A complete audio file (WebM with headers).

        Returns a dict with 'timestamp', 'speaker', and 'text' keys,
        or None if transcription produced no text.
        """
        if len(audio_data) < 1000:
            logger.warning(f"Audio chunk too small ({len(audio_data)} bytes), skipping")
            return None

        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"

            logger.info(f"Sending {len(audio_data)} bytes to Whisper model '{self._model}'...")

            response = await self.client.audio.transcriptions.create(
                model=self._model,
                file=audio_file,
                response_format="text",
                language="en",
            )

            text = response.strip() if isinstance(response, str) else response.text.strip()

            if not text:
                logger.info("Transcription returned empty text")
                return None

            logger.info(f"Transcription result: {text[:100]}...")

            return {
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "speaker": "Speaker",
                "text": text,
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
