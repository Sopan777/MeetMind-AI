from typing import List, Optional
from pydantic import BaseModel, Field

class SpeakerSegment(BaseModel):
    label: str
    start: float
    end: float
    confidence: float
    duration: float

class DiarizationResult(BaseModel):
    speakers: List[SpeakerSegment]
    num_speakers_detected: int
    was_overlap: bool
    inference_ms: int
    provider_version: str
