import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import setup_logging
from core.database import AsyncSessionLocal
from schemas.websocket import AudioMessage, ControlMessage
from schemas.events import MeetingEvent, EventType
from providers.transcription.factory import create_transcription_provider
from providers.analysis.factory import create_analyzer_provider
from providers.diarization.factory import create_diarization_provider
import numpy as np
from services.meeting_state import MeetingStateManager
from services.analyzer_scheduler import AnalyzerScheduler
from services.persistence import PersistenceService

# Import the existing REST app to mount it
from app.main import app as rest_app

# Set up structured logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Global session manager
session_manager = MeetingStateManager()

# Global schedulers (one per meeting)
schedulers: dict[str, AnalyzerScheduler] = {}

# C-1: Module-level GPU lock — shared across all concurrent WebSocket connections
_gpu_lock = asyncio.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up MeetingMind AI WebSocket Server...")
    
    # Create all database tables if they don't exist
    from core.database import engine
    from app.database import Base
    from app import models  # noqa: F401 — ensure all models are registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created.")
    
    # Health check and pre-load heavy ML models on startup
    transcriber = create_transcription_provider()
    analyzer = create_analyzer_provider()
    diarizer = create_diarization_provider()
    
    logger.info("Pre-loading ML models... This may take up to 30 seconds.")
    try:
        if hasattr(transcriber, '_get_model'):
            await transcriber._get_model()
        logger.info("Whisper model loaded successfully.")
    except Exception as e:
        logger.warning(f"Whisper model preload failed (will retry on first audio): {e}")
    
    try:
        if hasattr(diarizer, '_get_pipeline'):
            await diarizer._get_pipeline()
        logger.info("Pyannote model loaded successfully.")
    except Exception as e:
        logger.warning(f"Pyannote model preload failed (diarization will be disabled): {e}")
        
    logger.info(f"Transcriber health: {await transcriber.health_check()}")
    logger.info(f"Analyzer health: {await analyzer.health_check()}")
    
    yield
    
    logger.info("Shutting down...")

# Main FastAPI application for WebSockets
app = FastAPI(title="MeetingMind AI - Realtime", version="2.0.0", lifespan=lifespan)

# Mount the REST API
app.mount("/api", rest_app)

import uuid
from datetime import datetime, timezone

# M-1: Restrict CORS to env-configured origins (falls back to localhost for dev)
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()] if settings.CORS_ORIGINS else ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time meeting analysis using VAD utterance chunks.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    transcription_provider = create_transcription_provider()
    analyzer_provider = create_analyzer_provider()
    diarization_provider = create_diarization_provider()

    current_meeting_id = None
    # H-2: Track background persistence tasks so we can await them on disconnect
    _pending_tasks: set[asyncio.Task] = set()
    # H-4: Rate limiting — max frames per second per connection
    _frame_timestamps: list[float] = []
    _MAX_FRAMES_PER_SECOND = 5

    def _check_rate_limit() -> bool:
        now = time.monotonic()
        _frame_timestamps[:] = [t for t in _frame_timestamps if now - t < 1.0]
        if len(_frame_timestamps) >= _MAX_FRAMES_PER_SECOND:
            return False
        _frame_timestamps.append(now)
        return True

    # H-2: Persistence helpers that register in _pending_tasks
    async def bg_save_event(ev):
        try:
            async with AsyncSessionLocal() as session:
                await PersistenceService(session).save_event(ev)
        except Exception as e:
            logger.error(f"Failed to persist event {ev.id}: {e}")

    async def bg_save_profile(prof, mid):
        try:
            async with AsyncSessionLocal() as session:
                await PersistenceService(session).save_speaker_profile(prof, mid)
        except Exception as e:
            logger.error(f"Failed to persist speaker profile {prof.label}: {e}")

    async def bg_save_embedding(mid, eid, emb, lbl, dur):
        try:
            async with AsyncSessionLocal() as session:
                await PersistenceService(session).save_speaker_embedding(mid, eid, emb, lbl, dur)
        except Exception as e:
            logger.error(f"Failed to persist embedding for event {eid}: {e}")

    async def bg_save_insights(mid, insights):
        try:
            async with AsyncSessionLocal() as session:
                await PersistenceService(session).save_insights(mid, insights)
        except Exception as e:
            logger.error(f"Failed to persist insights for meeting {mid}: {e}")

    def _spawn(coro):
        task = asyncio.create_task(coro)
        _pending_tasks.add(task)
        task.add_done_callback(_pending_tasks.discard)
        return task

    try:
        # Wait for initial connect message
        while True:
            data = await websocket.receive()
            if "text" in data:
                try:
                    msg = json.loads(data["text"])
                    if msg.get("type") == "start" and msg.get("meeting_id"):
                        current_meeting_id = msg["meeting_id"]
                        await session_manager.get_session(current_meeting_id)
                        # Create the Meeting row before any events are saved (satisfies FK constraint)
                        async with AsyncSessionLocal() as _sess:
                            await PersistenceService(_sess).save_meeting(
                                current_meeting_id,
                                title=msg.get("title", "Live Recording"),
                            )
                        if current_meeting_id not in schedulers:
                            schedulers[current_meeting_id] = AnalyzerScheduler(current_meeting_id)
                        await websocket.send_json({"type": "status", "status": "connected"})
                        logger.info(f"Session started for meeting {current_meeting_id}")
                        break
                    elif msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except Exception as e:
                    logger.warning(f"Error parsing initial WS message: {e}")
            else:
                logger.warning("Received binary data before start control message")

        while True:
            data = await websocket.receive()

            if "text" in data:
                try:
                    msg = json.loads(data["text"])

                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})

                    elif msg.get("type") == "audio":
                        # H-4: Drop frames that exceed the rate limit
                        if not _check_rate_limit():
                            logger.warning(f"Rate limit exceeded for meeting {current_meeting_id}, dropping frame")
                            # Consume the following binary frame so framing stays in sync
                            await websocket.receive()
                            continue

                        seq = msg.get("sequence", 0)
                        speech_start_ms = msg.get("speech_start_ms", 0)
                        speech_end_ms = msg.get("speech_end_ms", 0)

                        bin_data = await websocket.receive()
                        if "bytes" not in bin_data:
                            logger.error("Expected binary audio frame after audio metadata")
                            continue

                        audio_chunk = bin_data["bytes"]
                        state = await session_manager.get_session(current_meeting_id)

                        if not state.validate_audio_sequence(seq):
                            continue

                        state.last_audio_sequence = max(state.last_audio_sequence, seq)
                        await websocket.send_json({"type": "status", "status": "processing"})

                        # C-3: Wrap the entire per-utterance block so one bad frame
                        # never terminates the session
                        try:
                            prompt = state.timeline.get_speech_text()[-1000:] if state.timeline.total_events > 0 else None

                            # C-1: Use the module-level _gpu_lock (shared across connections)
                            async def transcribe_with_lock():
                                async with _gpu_lock:
                                    return await transcription_provider.transcribe(audio_chunk, prompt)

                            async def diarize_with_lock():
                                async with _gpu_lock:
                                    return await diarization_provider.diarize(audio_chunk)

                            result, diarization_result = await asyncio.gather(
                                asyncio.create_task(transcribe_with_lock()),
                                asyncio.create_task(diarize_with_lock()),
                            )

                            # C-3: Null-check transcription before use
                            if result is None:
                                logger.warning(f"Transcription returned None for meeting {current_meeting_id}")
                                await websocket.send_json({"type": "status", "status": "recording"})
                                continue

                            # C-2: Use pyannote speaker labels directly; skip the
                            # speaker registry re-clustering which relied on dummy embeddings
                            speaker_label = "Unknown"
                            speaker_confidence = 1.0
                            resolved_embedding = None

                            if diarization_result and diarization_result.speakers:
                                if len(diarization_result.speakers) > 1:
                                    dominant = max(diarization_result.speakers, key=lambda s: s.duration)
                                    speaker_label = dominant.label
                                    speaker_confidence = dominant.confidence * 0.7
                                else:
                                    speaker = diarization_result.speakers[0]
                                    speaker_label = speaker.label
                                    speaker_confidence = speaker.confidence

                            speech_event = MeetingEvent(
                                id=str(uuid.uuid4()),
                                meeting_id=current_meeting_id,
                                event_type=EventType.SPEECH,
                                sequence=-1,
                                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                                speaker_label=speaker_label,
                                text=result.text,
                                speech_start_ms=speech_start_ms,
                                speech_end_ms=speech_end_ms,
                                duration_ms=int(result.duration_seconds * 1000),
                                language=result.language,
                                speaker_confidence=speaker_confidence,
                            )

                            state.entity_registry.process_text(result.text)
                            state.timeline.append(speech_event)
                            state.total_audio_seconds += result.duration_seconds

                            # H-2: Use _spawn so tasks are tracked and awaited on disconnect
                            _spawn(bg_save_event(speech_event))

                            await websocket.send_json({
                                "type": "transcript",
                                "data": {
                                    "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                                    "speaker": speaker_label,
                                    "confidence": speaker_confidence,
                                    "text": result.text,
                                },
                            })

                            scheduler = schedulers[current_meeting_id]
                            scheduler.on_speech_event(state, analyzer_provider, websocket, bg_save_insights)

                        except Exception as frame_err:
                            # C-3: Log but continue — one bad frame must not end the session
                            logger.error(f"Error processing audio frame (seq={seq}): {frame_err}", exc_info=True)
                            await websocket.send_json({"type": "error", "message": "Failed to process audio frame"})

                        await websocket.send_json({"type": "status", "status": "recording"})

                    elif msg.get("type") == "analyze_now":
                        state = await session_manager.get_session(current_meeting_id)
                        scheduler = schedulers[current_meeting_id]
                        scheduler.force_trigger(state, analyzer_provider, websocket, bg_save_insights)

                    elif msg.get("type") == "stop":
                        logger.info(f"Client requested stop for meeting {current_meeting_id}")
                        break

                except Exception as e:
                    logger.error(f"Error processing WS text frame: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected (meeting {current_meeting_id})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if current_meeting_id:
            await session_manager.end_session(current_meeting_id)
            if current_meeting_id in schedulers:
                del schedulers[current_meeting_id]
        # H-2: Drain pending persistence tasks before closing the session
        if _pending_tasks:
            logger.info(f"Waiting for {len(_pending_tasks)} pending persistence tasks...")
            await asyncio.gather(*list(_pending_tasks), return_exceptions=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
