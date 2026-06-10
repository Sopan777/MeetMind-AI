import asyncio
import logging
from datetime import datetime, timezone
from collections import deque
from typing import List, Optional

from schemas.events import MeetingEvent, EventType

logger = logging.getLogger(__name__)

class MeetingTimeline:
    """
    Timeline Buffer for Meeting Events.
    Maintains an ordered, append-only ring buffer of events for real-time analysis,
    while optionally queuing them for async database persistence.
    """
    
    def __init__(self, meeting_id: str, max_events: int = 5000):
        self.meeting_id = meeting_id
        self.max_events = max_events
        self.events: deque[MeetingEvent] = deque(maxlen=max_events)
        
        # Tracking counters
        self.total_events = 0
        self.speech_events = 0
        self.visual_events = 0
        self.insight_events = 0
        self.system_events = 0
        
        # Track when the last insight was generated
        self.last_insight_seq = -1
        
    def append(self, event: MeetingEvent) -> None:
        """Appends an event to the timeline."""
        event.sequence = self.total_events

        if self.total_events >= self.max_events and self.total_events % self.max_events == 0:
            logger.warning(
                f"Meeting {self.meeting_id}: timeline ring buffer full at {self.total_events} events — "
                "oldest events are being discarded. Long-meeting context may be incomplete."
            )

        self.events.append(event)
        self.total_events += 1
        
        if event.event_type == EventType.SPEECH:
            self.speech_events += 1
        elif event.event_type == EventType.VISUAL:
            self.visual_events += 1
        elif event.event_type == EventType.INSIGHT:
            self.insight_events += 1
            self.last_insight_seq = event.sequence
        elif event.event_type == EventType.SYSTEM:
            self.system_events += 1
            
    def get_recent(self, n: int, types: Optional[List[EventType]] = None) -> List[MeetingEvent]:
        """Returns the last N events, optionally filtered by type."""
        # Work backwards through the deque to find the most recent N matching events
        result = []
        for event in reversed(self.events):
            if types is None or event.event_type in types:
                result.insert(0, event)  # Keep chronological order
                if len(result) >= n:
                    break
        return result

    def get_since_sequence(self, seq: int, types: Optional[List[EventType]] = None) -> List[MeetingEvent]:
        """Returns all events after a specific sequence number."""
        result = []
        # Since events are strictly ordered by sequence, we can start from the end
        for event in reversed(self.events):
            if event.sequence <= seq:
                break
            if types is None or event.event_type in types:
                result.insert(0, event)
        return result

    def get_speech_text(self, since_seq: int = -1) -> str:
        """Convenience method to get all speech text since a sequence number."""
        events = self.get_since_sequence(since_seq, types=[EventType.SPEECH])
        texts = []
        for e in events:
            if e.text:
                speaker = e.speaker_label or "Speaker"
                # Parse the ISO string to a datetime object, handling the Z or +00:00 suffix
                try:
                    dt = datetime.fromisoformat(e.timestamp_utc.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except ValueError:
                    time_str = "00:00:00" # Fallback
                texts.append(f"[{time_str}] {speaker}: {e.text}")
        return "\n".join(texts)

    def speech_count_since_last_insight(self) -> int:
        """How many speech utterances have occurred since the last insight was generated?"""
        if self.last_insight_seq == -1:
            return self.speech_events
            
        count = 0
        for event in reversed(self.events):
            if event.sequence <= self.last_insight_seq:
                break
            if event.event_type == EventType.SPEECH:
                count += 1
        return count
