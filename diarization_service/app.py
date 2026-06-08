"""
Diarization Microservice
Runs on port 8001 with Python 3.12 + pyannote.audio 3.1.1 + numpy 1.26.4
Exposes POST /diarize which accepts a WAV file and returns speaker segments.
"""
import io
import os
import logging
import asyncio
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pyannote Diarization Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global pipeline singleton ---
_pipeline = None
_pipeline_lock = asyncio.Lock()

LOCAL_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "backend", "local_pyannote", "diarization", "config.yaml"
)

class SpeakerSegment(BaseModel):
    speaker: str
    start: float
    end: float
    duration: float
    confidence: float

class DiarizeResponse(BaseModel):
    speakers: List[SpeakerSegment]
    num_speakers: int

async def get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    async with _pipeline_lock:
        if _pipeline is not None:
            return _pipeline

        logger.info("Loading pyannote pipeline from local config...")
        try:
            import torchaudio
            if not hasattr(torchaudio, 'set_audio_backend'):
                torchaudio.set_audio_backend = lambda x: None
            if not hasattr(torchaudio, 'get_audio_backend'):
                torchaudio.get_audio_backend = lambda: "soundfile"
            
            import sys
            import types
            if 'torchaudio.backend' not in sys.modules:
                sys.modules['torchaudio.backend'] = types.ModuleType('torchaudio.backend')
                sys.modules['torchaudio.backend.common'] = types.ModuleType('torchaudio.backend.common')
                class AudioMetaData:
                    pass
                sys.modules['torchaudio.backend.common'].AudioMetaData = AudioMetaData


            from pyannote.audio import Pipeline
            import torch
            
            # Fix PyTorch 2.6 weights_only=True breaking Pyannote
            _original_load = torch.load
            def _patched_load(*args, **kwargs):
                kwargs['weights_only'] = False
                return _original_load(*args, **kwargs)
            torch.load = _patched_load

            config_path = os.path.abspath(LOCAL_CONFIG_PATH)
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config not found: {config_path}")

            _pipeline = Pipeline.from_pretrained(config_path)
            
            if torch.cuda.is_available():
                _pipeline.to(torch.device("cuda"))
                logger.info("Pyannote pipeline loaded successfully on CUDA!")
            else:
                _pipeline.to(torch.device("cpu"))
                logger.info("Pyannote pipeline loaded successfully on CPU!")
        except Exception as e:
            logger.error(f"Failed to load pipeline: {e}")
            raise

    return _pipeline


@app.get("/health")
async def health():
    return {"status": "ok", "pipeline_loaded": _pipeline is not None}


@app.post("/warmup")
async def warmup():
    """Pre-load the pipeline into memory."""
    try:
        await get_pipeline()
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diarize", response_model=DiarizeResponse)
async def diarize(audio: UploadFile = File(...)):
    """
    Accept a WAV file, run speaker diarization, return speaker segments.
    """
    try:
        pipeline = await get_pipeline()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Pipeline not available: {e}")

    audio_bytes = await audio.read()

    def run_diarization():
        import soundfile as sf
        import numpy as np
        import torch

        # Load audio from bytes
        audio_io = io.BytesIO(audio_bytes)
        data, samplerate = sf.read(audio_io, dtype="float32")

        # Ensure mono
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Resample to 16kHz if needed
        if samplerate != 16000:
            import torchaudio.functional as F
            tensor = torch.from_numpy(data).unsqueeze(0)
            tensor = F.resample(tensor, samplerate, 16000)
            data = tensor.squeeze(0).numpy()
            samplerate = 16000

        # Run pipeline
        audio_tensor = torch.from_numpy(data).unsqueeze(0)
        waveform_dict = {"waveform": audio_tensor, "sample_rate": samplerate}
        diarization = pipeline(waveform_dict)

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(SpeakerSegment(
                speaker=speaker,
                start=round(turn.start, 3),
                end=round(turn.end, 3),
                duration=round(turn.duration, 3),
                confidence=0.9  # pyannote 3.x doesn't expose per-segment confidence
            ))
        return segments

    loop = asyncio.get_event_loop()
    try:
        segments = await loop.run_in_executor(None, run_diarization)
        return DiarizeResponse(speakers=segments, num_speakers=len(set(s.speaker for s in segments)))
    except Exception as e:
        logger.error(f"Diarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, log_level="info")
