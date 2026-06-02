import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from services.llm_analyzer import LLMAnalyzer
from services.transcription import TranscriptionService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MeetingMind AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_transcription_service() -> TranscriptionService:
    api_key = os.getenv("WHISPER_API_KEY", "")
    api_url = os.getenv("WHISPER_API_URL", "https://api.openai.com/v1")
    return TranscriptionService(api_key=api_key, api_url=api_url)


def create_llm_analyzer() -> LLMAnalyzer:
    api_key = os.getenv("NVIDIA_API_KEY", "")
    api_url = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1")
    model = os.getenv("NVIDIA_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")
    return LLMAnalyzer(api_key=api_key, api_url=api_url, model=model)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """Main WebSocket endpoint for real-time meeting analysis.

    Protocol:
    - Client sends binary frames containing audio chunks (webm/opus).
    - Server sends JSON text frames with transcript updates and insights.

    Server messages have the shape:
      { "type": "transcript", "data": { "timestamp": "...", "speaker": "...", "text": "..." } }
      { "type": "insights", "data": { "action_items": [...], "decisions": [...], "risks": [...], "summary": "..." } }
      { "type": "error", "message": "..." }
      { "type": "status", "status": "connected" | "processing" }
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    transcription_service = create_transcription_service()
    llm_analyzer = create_llm_analyzer()

    # Send initial connected status
    await websocket.send_json({"type": "status", "status": "connected"})

    # Background task: periodically run LLM analysis
    analysis_running = True

    async def run_periodic_analysis():
        while analysis_running:
            await asyncio.sleep(5)
            if llm_analyzer.should_analyze():
                try:
                    insights = await llm_analyzer.analyze()
                    if insights:
                        await websocket.send_json({
                            "type": "insights",
                            "data": insights.model_dump(),
                        })
                except Exception as e:
                    logger.error(f"Analysis task error: {e}")

    analysis_task = asyncio.create_task(run_periodic_analysis())

    try:
        while True:
            # Receive binary audio data from client
            data = await websocket.receive()

            if "bytes" in data and data["bytes"]:
                audio_chunk = data["bytes"]

                # Each chunk from the frontend is a complete, self-contained
                # audio file (WebM with headers), so transcribe it directly.
                await websocket.send_json({"type": "status", "status": "processing"})

                result = await transcription_service.transcribe(audio_chunk)

                if result:
                    # Send transcript to client
                    await websocket.send_json({
                        "type": "transcript",
                        "data": result,
                    })

                    # Feed transcript to LLM analyzer
                    llm_analyzer.add_transcript(result)

                await websocket.send_json({"type": "status", "status": "recording"})

            elif "text" in data and data["text"]:
                # Handle text messages (e.g., control commands)
                try:
                    msg = json.loads(data["text"])
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        analysis_running = False
        analysis_task.cancel()
        try:
            await analysis_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
