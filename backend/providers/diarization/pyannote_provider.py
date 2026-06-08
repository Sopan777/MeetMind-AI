"""
HTTP-based Diarization Provider.
Calls the standalone diarization_service (Python 3.12 + pyannote 3.1.1)
over HTTP instead of importing pyannote directly, avoiding all dependency conflicts.
"""
import io
import wave
import logging
import asyncio
from typing import Optional, Dict, Any

import httpx

from core.config import settings
from schemas.diarization import DiarizationResult, SpeakerSegment
from .base import DiarizationProvider

logger = logging.getLogger(__name__)

DIARIZATION_SERVICE_URL = "http://127.0.0.1:8001"


class PyannoteDiarizationProvider(DiarizationProvider):
    """
    Diarization provider that calls the standalone pyannote microservice over HTTP.
    The microservice runs in its own Python 3.12 + pyannote.audio 3.1.1 environment.
    """

    def __init__(self):
        self.device = settings.DIARIZATION_DEVICE
        self.service_url = DIARIZATION_SERVICE_URL
        self.version = "pyannote-3.1-http"
        self._client: Optional[httpx.AsyncClient] = None
        self._available: Optional[bool] = None  # None = not checked yet
        logger.info(f"Initialized HTTP DiarizationProvider → {self.service_url}")

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def _get_pipeline(self):
        """Check service availability (used by preloader in main.py)."""
        available = await self._check_service()
        return available or None

    async def _check_service(self) -> bool:
        """Returns True if the diarization microservice is reachable."""
        if self._available is True:
            return True
        try:
            r = await self._get_client().get(f"{self.service_url}/health", timeout=3.0)
            self._available = r.status_code == 200
        except Exception:
            self._available = False
        if not self._available:
            logger.warning(
                "Diarization microservice not reachable at %s. "
                "Speaker labels will be 'Unknown'. "
                "Start it with: diarization_service\\start.bat",
                self.service_url,
            )
        return self._available

    async def diarize(self, audio_bytes: bytes) -> Optional[DiarizationResult]:
        # Skip very short clips
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                duration = wf.getnframes() / wf.getframerate()
                if duration < 1.5:
                    return None
        except Exception:
            return None

        if not await self._check_service():
            return None

        try:
            response = await self._get_client().post(
                f"{self.service_url}/diarize",
                files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
                timeout=90.0,
            )
            response.raise_for_status()
            data = response.json()

            segments = [
                SpeakerSegment(
                    label=s["speaker"],
                    start=s["start"],
                    end=s["end"],
                    confidence=s["confidence"],
                    duration=s["duration"],
                )
                for s in data.get("speakers", [])
            ]

            if not segments:
                return None

            return DiarizationResult(
                speakers=segments,
                num_speakers_detected=data.get("num_speakers", len(segments)),
                was_overlap=data.get("num_speakers", 1) > 1,
                inference_ms=0,
                provider_version=self.version,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Diarization service returned error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error calling diarization service: {e}")
            self._available = None  # re-check on next call
            return None

    async def health_check(self) -> Dict[str, Any]:
        available = await self._check_service()
        return {
            "provider": "pyannote-http",
            "service_url": self.service_url,
            "service_available": available,
            "device": self.device,
        }
