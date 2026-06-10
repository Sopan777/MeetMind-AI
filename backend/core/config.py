from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "MeetingMind AI"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./meetingmind.db"
    SYNC_DATABASE_URL: str = "sqlite:///./meetingmind.db"

    # Transcription settings
    TRANSCRIPTION_PROVIDER: str = "groq"  # local | groq | openai
    LOCAL_WHISPER_MODEL: str = "distil-large-v3"
    LOCAL_WHISPER_DEVICE: str = "cuda"
    LOCAL_WHISPER_COMPUTE_TYPE: str = "float16"
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # LLM Analyzer settings
    ANALYZER_PROVIDER: str = "nvidia"  # nvidia | gemini
    NVIDIA_API_KEY: str = ""
    NVIDIA_API_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/llama-3.3-nemotron-super-49b-v1"
    GEMINI_API_KEY: str = ""

    # Diarization
    DIARIZATION_PROVIDER: str = "pyannote"
    DIARIZATION_DEVICE: str = "cpu"
    # H-3: Configurable URL for the pyannote microservice (different host/port from backend)
    DIARIZATION_SERVICE_URL: str = "http://127.0.0.1:8002"
    HF_TOKEN: str = ""

    # Application tuning
    MAX_UTTERANCE_DURATION_SECONDS: int = 15

    # Timeline settings
    TIMELINE_MAX_EVENTS: int = 5000

    # Analyzer scheduler
    EXTRACTION_UTTERANCE_THRESHOLD: int = 15
    SUMMARY_UTTERANCE_THRESHOLD: int = 45
    ANALYZER_MIN_INTERVAL_SECONDS: int = 20

    # Context builder
    TIER1_MAX_EVENTS: int = 20
    TIER1_MAX_AGE_SECONDS: int = 300
    TIER2_MAX_TOKENS: int = 600
    TIER3_MAX_TOKENS: int = 500

    # Security
    # H-1: No default — app refuses to start if SECRET_KEY is not set in environment
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # M-1: Comma-separated list of allowed CORS origins; empty = localhost dev default
    CORS_ORIGINS: str = ""

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if not v or v == "change-in-production":
            raise ValueError(
                "SECRET_KEY must be set to a strong random value via environment variable. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
