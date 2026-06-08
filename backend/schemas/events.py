from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

class EventType(str, Enum):
    SPEECH = "speech"
    VISUAL = "visual"
    INSIGHT = "insight"
    SYSTEM = "system"

class InsightType(str, Enum):
    ACTION_ITEM = "action_item"
    DECISION = "decision"
    RISK = "risk"
    SUMMARY = "summary"

class MeetingEvent(BaseModel):
    id: str
    meeting_id: str
    event_type: EventType
    sequence: int
    timestamp_utc: str  # ISO format string for easy serialization
    
    # Speech fields
    speaker_label: Optional[str] = None
    text: Optional[str] = None
    speech_start_ms: Optional[int] = None
    speech_end_ms: Optional[int] = None
    duration_ms: Optional[int] = None
    transcription_confidence: Optional[float] = None
    speaker_confidence: Optional[float] = None
    language: Optional[str] = None
    
    # Visual fields
    screenshot_path: Optional[str] = None
    content_type: Optional[str] = None
    description: Optional[str] = None
    text_detected: Optional[List[str]] = None
    perceptual_hash: Optional[str] = None
    
    # Insight fields
    insight_type: Optional[InsightType] = None
    content_json: Optional[str] = None
    source_event_range: Optional[Tuple[int, int]] = None  # (start_seq, end_seq)
    
    # System fields
    system_event: Optional[str] = None
    metadata_json: Optional[str] = None

    class Config:
        use_enum_values = True
