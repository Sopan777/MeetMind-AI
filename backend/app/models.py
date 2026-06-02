import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Employee")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    meetings = relationship("Meeting", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="meetings")
    transcripts = relationship("Transcript", back_populates="meeting")
    action_items = relationship("ActionItem", back_populates="meeting")
    decisions = relationship("Decision", back_populates="meeting")
    risks = relationship("Risk", back_populates="meeting")


class Transcript(Base):
    __tablename__ = "transcripts"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    speaker = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    meeting = relationship("Meeting", back_populates="transcripts")


class ActionItem(Base):
    __tablename__ = "action_items"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    task = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    deadline = Column(String, nullable=False)
    status = Column(String, default="todo")
    priority = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    meeting = relationship("Meeting", back_populates="action_items")


class Decision(Base):
    __tablename__ = "decisions"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    decided_by = Column(String, nullable=False)
    impact = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    meeting = relationship("Meeting", back_populates="decisions")


class Risk(Base):
    __tablename__ = "risks"
    id = Column(String, primary_key=True)
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="medium")
    impact = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    detected_phrase = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    meeting = relationship("Meeting", back_populates="risks")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="notifications")


class Integration(Base):
    __tablename__ = "integrations"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    connected = Column(Boolean, default=False)
    config_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ModelMetric(Base):
    __tablename__ = "model_metrics"
    id = Column(String, primary_key=True)
    model_version = Column(String, nullable=False)
    accuracy = Column(Float, nullable=False)
    inference_count = Column(Integer, default=0)
    avg_latency = Column(Float, default=0)
    failure_rate = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
