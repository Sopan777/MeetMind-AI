from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MeetingMind AI"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./meetingmind.db"
    
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
    DIARIZATION_DEVICE: str = "cpu" # Recommended CPU to not block Whisper
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
    SECRET_KEY: str = "change-in-production"
    ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
