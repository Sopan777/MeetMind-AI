import uuid
import logging
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import MeetingEvent, Speaker, SpeakerEmbedding, DiarizationResultLog, ActionItem as DBActionItem, Decision as DBDecision, Risk as DBRisk
from schemas.analysis import MeetingInsights
from schemas.transcription import TranscriptionResult

logger = logging.getLogger(__name__)

class PersistenceService:
    """Handles asynchronous database operations for the real-time meeting pipeline."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def save_event(self, event) -> None:
        """
        Saves a single meeting event to the database.
        Note: event should be the Pydantic model schemas.events.MeetingEvent
        """
        db_event = MeetingEvent(
            id=event.id,
            meeting_id=event.meeting_id,
            event_type=event.event_type.value if hasattr(event.event_type, "value") else event.event_type,
            sequence=event.sequence,
            timestamp_utc=datetime.fromisoformat(event.timestamp_utc.replace('Z', '+00:00')) if isinstance(event.timestamp_utc, str) else event.timestamp_utc,
            
            speaker_label=event.speaker_label,
            text=event.text,
            speech_start_ms=event.speech_start_ms,
            speech_end_ms=event.speech_end_ms,
            duration_ms=event.duration_ms,
            transcription_confidence=event.transcription_confidence,
            speaker_confidence=event.speaker_confidence,
            language=event.language,
            
            screenshot_path=event.screenshot_path,
            content_type=event.content_type,
            description=event.description,
            perceptual_hash=event.perceptual_hash,
            
            insight_type=event.insight_type.value if hasattr(event.insight_type, "value") else event.insight_type,
            content_json=event.content_json,
            
            system_event=event.system_event,
            metadata_json=event.metadata_json
        )
        
        self.db.add(db_event)
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to persist event: {e}")
            raise

    async def save_speaker_profile(self, profile, meeting_id: str) -> None:
        """Upserts a Speaker profile based on label and meeting_id."""
        import json
        
        # Check if exists
        query = select(Speaker).where(Speaker.meeting_id == meeting_id, Speaker.label == profile.label)
        result = await self.db.execute(query)
        db_speaker = result.scalars().first()
        
        if not db_speaker:
            db_speaker = Speaker(
                id=str(uuid.uuid4()),
                meeting_id=meeting_id,
                label=profile.label,
                color_hex="#94A3B8" # Will be calculated by frontend
            )
            self.db.add(db_speaker)
            
        db_speaker.total_utterances = profile.sample_count
        db_speaker.total_speak_secs = profile.total_speaking_seconds
        db_speaker.first_seen_at = profile.first_seen_at
        db_speaker.last_seen_at = profile.last_seen_at
        
        if profile.centroid is not None:
            # Simple list serialization for sqlite
            db_speaker.centroid_blob = json.dumps(profile.centroid.tolist())
            db_speaker.centroid_samples = profile.sample_count
            
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to persist speaker profile: {e}")

    async def save_insights(self, meeting_id: str, insights) -> None:
        """Persists extracted insights (action items, decisions, risks) to the database."""
        import uuid as _uuid
        try:
            for item in insights.action_items:
                db_item = DBActionItem(
                    id=str(_uuid.uuid4()),
                    meeting_id=meeting_id,
                    task=item.task,
                    owner=item.owner,
                    deadline=item.deadline,
                    quote=item.quote,
                    confidence=item.confidence,
                    review_status=item.review_status,
                )
                self.db.add(db_item)

            for item in insights.decisions:
                db_item = DBDecision(
                    id=str(_uuid.uuid4()),
                    meeting_id=meeting_id,
                    decision=item.decision,
                    timestamp=item.timestamp,
                    quote=item.quote,
                    confidence=item.confidence,
                )
                self.db.add(db_item)

            for item in insights.risks:
                db_item = DBRisk(
                    id=str(_uuid.uuid4()),
                    meeting_id=meeting_id,
                    description=item.description,
                    timestamp=item.timestamp,
                    quote=item.quote,
                    confidence=item.confidence,
                )
                self.db.add(db_item)

            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to persist insights: {e}")


        """Saves a raw embedding for an utterance."""
        import json
        
        # We need the speaker's DB ID
        query = select(Speaker.id).where(Speaker.meeting_id == meeting_id, Speaker.label == speaker_label)
        result = await self.db.execute(query)
        speaker_id = result.scalars().first()
        
        db_embed = SpeakerEmbedding(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            speaker_id=speaker_id,
            event_id=event_id,
            timestamp_utc=datetime.now(timezone.utc),
            embedding_blob=json.dumps(embedding.tolist()) if embedding is not None else "[]",
            utterance_dur_ms=duration_ms
        )
        self.db.add(db_embed)
        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to persist speaker embedding: {e}")
