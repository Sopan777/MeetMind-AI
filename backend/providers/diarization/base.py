from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from schemas.diarization import DiarizationResult

class DiarizationProvider(ABC):
    """Abstract base class for speaker diarization providers."""
    
    @abstractmethod
    async def diarize(self, audio_bytes: bytes) -> Optional[DiarizationResult]:
        """
        Process audio and return speaker segments.
        Should handle its own execution logic (e.g. run_in_executor for CPU bounds).
        """
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return provider health status."""
        pass
