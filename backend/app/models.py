import datetime
from datetime import timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

_utcnow = lambda: datetime.datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Employee")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    meetings = relationship("Meeting", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    date = Column(String, nullable=False)
    duration = Column(Integer, default=0)
    status = Column(String, default="processing")
    type = Column(String, default="standup")
    quality_score = Column(Integer, default=0)
    participants = Column(Text, default="[]")  # JSON string
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    user = relationship("User", back_populates="meetings")
    events = relationship("MeetingEvent", back_populates="meeting")
    snapshots = relationship("AnalyzerSnapshot", back_populates="meeting")


class MeetingEvent(Base):
    __tablename__ = "meeting_events"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    sequence = Column(Integer, nullable=False, index=True)
    timestamp_utc = Column(DateTime(timezone=True), default=_utcnow, index=True)

    speaker_label = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    speech_start_ms = Column(Integer, nullable=True)
    speech_end_ms = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    transcription_confidence = Column(Float, nullable=True)
    speaker_confidence = Column(Float, nullable=True)
    language = Column(String, nullable=True)

    screenshot_path = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    perceptual_hash = Column(String, nullable=True)

    insight_type = Column(String, nullable=True)
    content_json = Column(Text, nullable=True)

    system_event = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)

    meeting = relationship("Meeting", back_populates="events")

class Speaker(Base):
    __tablename__ = "speakers"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    label = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    color_hex = Column(String, nullable=False)

    is_enrolled = Column(Boolean, default=False)
    enrolled_at = Column(DateTime(timezone=True), nullable=True)

    total_utterances = Column(Integer, default=0)
    total_speak_secs = Column(Float, default=0.0)
    first_seen_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)

    centroid_blob = Column(Text, nullable=True)
    centroid_dim = Column(Integer, default=256)
    centroid_samples = Column(Integer, default=0)

class SpeakerEmbedding(Base):
    __tablename__ = "speaker_embeddings"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    speaker_id = Column(String, ForeignKey("speakers.id"), nullable=True, index=True)
    event_id = Column(String, ForeignKey("meeting_events.id"), nullable=True)

    timestamp_utc = Column(DateTime(timezone=True), nullable=False)
    embedding_blob = Column(Text, nullable=False)

    utterance_dur_ms = Column(Integer, nullable=False)
    similarity_score = Column(Float, nullable=True)
    was_overlap = Column(Boolean, default=False)
    confidence = Column(Float, nullable=True)

class DiarizationResultLog(Base):
    __tablename__ = "diarization_results"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    event_id = Column(String, ForeignKey("meeting_events.id"), nullable=True)

    raw_segments_json = Column(Text, nullable=False)
    num_speakers_det = Column(Integer, nullable=False)
    was_overlap = Column(Boolean, default=False)
    dominant_speaker = Column(String, nullable=False)

    resolved_label = Column(String, nullable=False)
    resolution_sim = Column(Float, nullable=True)

    inference_ms = Column(Integer, nullable=True)
    provider_version = Column(String, nullable=True)


class AnalyzerSnapshot(Base):
    __tablename__ = "analyzer_snapshots"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    timestamp_utc = Column(DateTime(timezone=True), default=_utcnow)
    channel = Column(String, nullable=False)

    prompt_text = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, nullable=True)

    response_text = Column(Text, nullable=True)
    response_tokens = Column(Integer, nullable=True)

    action_items_json = Column(Text, nullable=True)
    decisions_json = Column(Text, nullable=True)
    risks_json = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=True)

    latency_ms = Column(Integer, nullable=True)
    model_name = Column(String, nullable=True)
    cost_estimate = Column(Float, nullable=True)

    event_seq_start = Column(Integer, nullable=True)
    event_seq_end = Column(Integer, nullable=True)

    meeting = relationship("Meeting", back_populates="snapshots")


class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    speaker = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    text = Column(Text, nullable=False)


class ActionItem(Base):
    __tablename__ = "action_items"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    task = Column(Text, nullable=False)
    owner = Column(String, nullable=False)
    deadline = Column(String, nullable=False)
    status = Column(String, default="todo")
    priority = Column(String, default="medium")


class Decision(Base):
    __tablename__ = "decisions"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    decided_by = Column(String, nullable=False)
    impact = Column(String, default="medium")


class Risk(Base):
    __tablename__ = "risks"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="medium")
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    detected_phrase = Column(String, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    user = relationship("User", back_populates="notifications")


class Integration(Base):
    __tablename__ = "integrations"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    connected = Column(Boolean, default=False)
    config_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class ModelMetric(Base):
    __tablename__ = "model_metrics"
    id = Column(String, primary_key=True)
    model_version = Column(String, nullable=False)
    accuracy = Column(Float, nullable=False)
    inference_count = Column(Integer, default=0)
    avg_latency = Column(Float, default=0)
    failure_rate = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
