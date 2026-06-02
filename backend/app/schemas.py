from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# --- Auth ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPassword(BaseModel):
    email: str


# --- Meetings ---
class MeetingCreate(BaseModel):
    title: str
    date: str
    duration: int = 0
    type: str = "standup"
    participants: list[str] = []

class MeetingResponse(BaseModel):
    id: str
    title: str
    date: str
    duration: int
    status: str
    type: str
    quality_score: int
    participants: str  # JSON string
    class Config:
        from_attributes = True

class TranscriptResponse(BaseModel):
    id: str
    speaker: str
    timestamp: str
    text: str
    class Config:
        from_attributes = True


# --- Action Items ---
class ActionItemCreate(BaseModel):
    meeting_id: str
    task: str
    owner: str
    deadline: str
    priority: str = "medium"

class ActionItemUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    owner: Optional[str] = None

class ActionItemResponse(BaseModel):
    id: str
    meeting_id: str
    task: str
    owner: str
    deadline: str
    status: str
    priority: str
    class Config:
        from_attributes = True


# --- Decisions ---
class DecisionResponse(BaseModel):
    id: str
    meeting_id: str
    title: str
    description: str
    decided_by: str
    impact: str
    class Config:
        from_attributes = True


# --- Risks ---
class RiskResponse(BaseModel):
    id: str
    meeting_id: str
    title: str
    description: str
    severity: str
    impact: Optional[str]
    recommendation: Optional[str]
    detected_phrase: Optional[str]
    class Config:
        from_attributes = True


# --- Notifications ---
class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    class Config:
        from_attributes = True


# --- Analytics ---
class AnalyticsOverview(BaseModel):
    total_meetings: int
    total_action_items: int
    total_decisions: int
    total_risks: int
    hours_saved: float

class MeetingSummaryResponse(BaseModel):
    executive: str
    technical: str
    client: str
