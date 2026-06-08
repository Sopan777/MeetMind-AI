import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict

from .meeting_timeline import MeetingTimeline
from .speaker_registry import SpeakerRegistry
from .entity_registry import EntityRegistry

logger = logging.getLogger(__name__)

class MeetingState:
    """Tracks state for an active WebSocket meeting audio session."""
    
    def __init__(self, meeting_id: str):
        self.meeting_id = meeting_id
        self.started_at_utc = datetime.now(timezone.utc)
        self.is_active = True
        self.timeline = MeetingTimeline(meeting_id)
        self.speaker_registry = SpeakerRegistry(meeting_id)
        self.entity_registry = EntityRegistry()
        
        # Audio tracking
        self.total_audio_seconds: float = 0.0
        
        # WebSocket sequence validation (deduplication)
        self.last_audio_sequence: int = -1
        self.seen_audio_sequences: set[int] = set()
        
        # Lock for async operations
        self.lock = asyncio.Lock()
        
    def validate_audio_sequence(self, seq: int) -> bool:
        """
        Check if audio sequence is valid (not duplicated, mostly in order).
        Returns True if valid, False if duplicate.
        """
        if seq in self.seen_audio_sequences:
            logger.warning(f"Duplicate audio sequence {seq} for meeting {self.meeting_id}")
            return False
            
        if seq < self.last_audio_sequence:
            logger.warning(f"Out-of-order sequence {seq} for meeting {self.meeting_id} (last: {self.last_audio_sequence})")
            
        self.seen_audio_sequences.add(seq)
        
        # Prevent unbounded growth for very long meetings
        if len(self.seen_audio_sequences) > 1000:
            min_seq = min(self.seen_audio_sequences)
            for i in range(min_seq, min_seq + 500):
                self.seen_audio_sequences.discard(i)
                
        return True


class MeetingStateManager:
    """Thread-safe manager for active meeting sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, MeetingState] = {}
        self._lock = asyncio.Lock()
        
    async def get_session(self, meeting_id: str) -> MeetingState:
        """Get or create a meeting session."""
        async with self._lock:
            if meeting_id not in self._sessions:
                logger.info(f"Creating new meeting state session for {meeting_id}")
                self._sessions[meeting_id] = MeetingState(meeting_id)
            return self._sessions[meeting_id]
            
    async def end_session(self, meeting_id: str):
        """End and cleanup a meeting session."""
        async with self._lock:
            if meeting_id in self._sessions:
                session = self._sessions[meeting_id]
                session.is_active = False
                logger.info(
                    f"Ended meeting session {meeting_id}. "
                    f"Total events: {session.timeline.total_events}, "
                    f"Audio processed: {session.total_audio_seconds:.1f}s"
                )
                del self._sessions[meeting_id]
