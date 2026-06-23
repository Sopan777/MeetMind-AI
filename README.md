# MeetMind AI

A real-time AI Meeting Intelligence Platform that captures screen/audio, generates live transcripts, and extracts action items, decisions, and risks — all while you meet.

## Clone

```bash
git clone https://github.com/Sopan777/MeetMind-AI.git
cd MeetMind-AI
```

## What it does

Share a browser tab, Zoom window, or system audio and MeetingMind:

- Transcribes speech live using Groq Whisper (or local faster-whisper)
- Identifies speakers via a pyannote diarization microservice
- Runs three parallel LLM agents every N utterances to extract:
  - **Action items** (owner + deadline + verbatim evidence quote)
  - **Decisions** (with confidence score)
  - **Risks**
  - **Rolling summary** (map-reduce chunking, never overflows context)
- Deduplicates extracted items in real time using semantic similarity
- Streams everything to the browser over WebSocket

## Architecture

```
Browser (Next.js 16)
  └─ Silero VAD (ONNX, client-side)
  └─ WAV encoder → WebSocket frames
         │
         ▼
Backend WebSocket server  (FastAPI, port 8001)
  ├─ asyncio.gather ──► Groq Whisper  (transcription)
  │                └──► pyannote HTTP  (diarization, port 8002)
  ├─ MeetingTimeline (in-memory ring buffer)
  ├─ EntityRegistry  (pronoun disambiguation)
  ├─ AnalyzerScheduler
  │     ├─ Action Agent  ─┐
  │     ├─ Decision Agent ─┼─► NVIDIA Nemotron / Gemini
  │     └─ Summary Agent ─┘
  └─ PersistenceService  (SQLite dev / PostgreSQL prod)
         │
         ▼
REST API  (FastAPI, mounted at /api)
  └─ meetings, transcripts, action-items, decisions, risks, auth
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, Tailwind CSS, shadcn/ui |
| VAD | `@ricky0123/vad-web` (Silero v5 ONNX, runs in browser) |
| Transcription | Groq Whisper / OpenAI Whisper / local faster-whisper |
| Diarization | pyannote.audio 3.1 HTTP microservice (optional) |
| Analysis LLM | NVIDIA Build API (Nemotron 49B) or Google Gemini |
| Backend | Python 3.12, FastAPI, uvicorn, asyncio |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy 2 async |
| Auth | JWT (python-jose) + bcrypt (passlib) |

## Quick start

### Prerequisites

- Python 3.12 (3.13 also works)
- Node.js 18+
- API keys: [Groq](https://console.groq.com) (free) + [NVIDIA Build](https://build.nvidia.com)

### 1. Configure environment

```bash
cp .env.example .env
```

Generate a secret key and paste it into `.env`:

```bash 
python -c "import secrets; print(secrets.token_hex(32))"
```

Minimum required entries in `.env`:

```env
SECRET_KEY=<generated above>
GROQ_API_KEY=<from console.groq.com — free tier works>
NVIDIA_API_KEY=<from build.nvidia.com>
```

### 2. Backend — create venv and install dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Start the backend

```bash
cd backend
# activate venv first (see step 2), then:
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Backend API docs: http://localhost:8001/api/docs

### 4. Start the frontend

```bash
cd frontend
npm install   # first time only
npm run dev
```

Runs on http://localhost:3000

### 5. Open the app

1. Go to http://localhost:3000
2. Click **Start Meeting Analysis**
3. Click **Start Analysis**, then share your screen — check **"Share tab audio"** in the browser dialog
4. Speak; the transcript and insights panels update live

## Configuration

All settings are driven by environment variables (see `.env.example`).

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | **required** | JWT signing key — generate with `secrets.token_hex(32)` |
| `GROQ_API_KEY` | `""` | Groq API key for Whisper transcription |
| `NVIDIA_API_KEY` | `""` | NVIDIA Build API key for Nemotron analysis |
| `HF_TOKEN` | `""` | Hugging Face token for pyannote diarization model |
| `TRANSCRIPTION_PROVIDER` | `groq` | `groq` \| `openai` \| `local` |
| `ANALYZER_PROVIDER` | `nvidia` | `nvidia` \| `gemini` |
| `DIARIZATION_SERVICE_URL` | `http://127.0.0.1:8002` | URL of the pyannote microservice |
| `CORS_ORIGINS` | `""` | Comma-separated allowed origins (empty = localhost:3000) |
| `DATABASE_URL` | SQLite | Use `postgresql+asyncpg://...` in production |

## Docker

```bash
# Set SECRET_KEY in .env first, then:
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8001
- PostgreSQL: localhost:5432

The compose file requires `SECRET_KEY` to be set in `.env` and will refuse to start without it.

## Speaker diarization (optional)

Speaker identification requires the pyannote microservice running separately on port 8002. Without it the system still works — all speakers show as `SPEAKER_00`, `SPEAKER_01`, etc. from pyannote's output, or `Unknown` if diarization is fully disabled.

To start the microservice:

```bash
cd diarization_service
# Requires Python 3.12 + pyannote.audio 3.1.1 + HF_TOKEN in .env
python service.py
```

## Local Whisper (optional, requires NVIDIA GPU)

```env
TRANSCRIPTION_PROVIDER=local
LOCAL_WHISPER_MODEL=distil-large-v3
LOCAL_WHISPER_DEVICE=cuda
LOCAL_WHISPER_COMPUTE_TYPE=float16
```

Requires CUDA toolkit and ≥6 GB VRAM.

## Security notes

- `SECRET_KEY` has no default — the app refuses to start without it
- CORS origins are env-configured; wildcard is rejected in all non-dev paths
- JWT tokens expire after 7 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Transcripts are treated as untrusted data in LLM prompts (injection-resistant delimiters)
- WebSocket connections are rate-limited to 5 audio frames/second per connection
