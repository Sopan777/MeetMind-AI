from core.config import settings
from .base import DiarizationProvider

def create_diarization_provider() -> DiarizationProvider:
    provider_name = settings.DIARIZATION_PROVIDER.lower()
    
    if provider_name == "pyannote":
        from .pyannote_provider import PyannoteDiarizationProvider
        return PyannoteDiarizationProvider()
    else:
        # Default or fallback dummy provider if needed
        from .pyannote_provider import PyannoteDiarizationProvider
        return PyannoteDiarizationProvider()
