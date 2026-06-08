import io
import os
import sys
import wave
import logging
import asyncio
from typing import Optional, Dict, Any

# Register NVIDIA CUDA DLL directories so CTranslate2 can find cublas64_12.dll
# The nvidia-cublas-cu12 pip package installs DLLs in a non-standard location
_venv_nvidia_dirs = [
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cublas", "bin"),
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cudnn", "bin"),
    os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "cuda_nvrtc", "bin"),
]
for _dll_dir in _venv_nvidia_dirs:
    if os.path.isdir(_dll_dir):
        os.add_dll_directory(_dll_dir)
        os.environ["PATH"] = _dll_dir + os.pathsep + os.environ.get("PATH", "")

from core.config import settings
from schemas.transcription import TranscriptionResult
from .base import TranscriptionProvider

logger = logging.getLogger(__name__)

# Global singleton for the model to ensure it's loaded only once
_model_instance = None
_model_lock = asyncio.Lock()

class LocalWhisperProvider(TranscriptionProvider):
    """Transcription provider using local faster-whisper with CUDA support."""
    
    def __init__(self):
        self.model_size = settings.LOCAL_WHISPER_MODEL
        self.device = settings.LOCAL_WHISPER_DEVICE
        self.compute_type = settings.LOCAL_WHISPER_COMPUTE_TYPE
        logger.info(f"Initialized LocalWhisperProvider placeholder for {self.model_size} on {self.device}")

    async def _get_model(self):
        global _model_instance
        if _model_instance is not None:
            return _model_instance
            
        async with _model_lock:
            if _model_instance is not None:
                return _model_instance
                
            logger.info("Loading local faster-whisper model... This may take a moment.")
            try:
                # Import here to avoid overhead if this provider isn't used
                from faster_whisper import WhisperModel
                
                # Run loading synchronously to avoid asyncio threading bugs with ctranslate2
                _model_instance = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                logger.info("Successfully loaded local Whisper model.")
            except ImportError:
                logger.error("faster-whisper is not installed. Please install it to use local transcription.")
                raise
            except Exception as e:
                logger.error(f"Error loading local Whisper model: {e}")
                raise
                
        return _model_instance

    def _decode_wav_to_float32(self, audio_bytes: bytes):
        import numpy as np
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            data = wf.readframes(n_frames)
            
            # Assuming 16-bit PCM mono
            samples = np.frombuffer(data, dtype=np.int16)
            # Convert to float32 normalized [-1.0, 1.0]
            float_samples = samples.astype(np.float32) / 32768.0
            return float_samples, framerate

    def _sync_transcribe(self, model, audio_bytes: bytes, prompt: Optional[str]) -> Optional[TranscriptionResult]:
        try:
            samples, framerate = self._decode_wav_to_float32(audio_bytes)
            
            # Resample if not 16000Hz (simplified assuming we always receive 16kHz from frontend)
            if framerate != 16000:
                logger.warning(f"Audio framerate is {framerate}, expected 16000. Transcription quality may degrade.")
            
            # Calculate duration
            duration = len(samples) / framerate
            
            kwargs = {
                "vad_filter": True,
                "language": "en"
            }
            if prompt:
                kwargs["initial_prompt"] = prompt[:200]
                
            segments, info = model.transcribe(samples, **kwargs)
            
            text = " ".join([segment.text for segment in segments]).strip()
            
            if not text:
                return None
                
            return TranscriptionResult(
                text=text,
                language=info.language,
                duration_seconds=duration,
                provider="local"
            )
        except Exception as e:
            logger.error(f"Local transcription error: {e}")
            return None

    async def transcribe(self, audio_bytes: bytes, prompt: Optional[str] = None) -> Optional[TranscriptionResult]:
        if len(audio_bytes) < 100:
            return None
            
        try:
            model = await self._get_model()
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_transcribe, model, audio_bytes, prompt)
        except Exception as e:
            logger.error(f"Error in transcribe execution: {e}", extra={"operation": "transcribe_local"})
            return None

    async def health_check(self) -> Dict[str, Any]:
        health = {
            "provider": "local",
            "model": self.model_size,
            "device": self.device,
            "loaded": _model_instance is not None
        }
        
        if self.device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    health["gpu_memory_allocated"] = torch.cuda.memory_allocated()
                    health["gpu_memory_reserved"] = torch.cuda.memory_reserved()
            except ImportError:
                pass
                
        return health
