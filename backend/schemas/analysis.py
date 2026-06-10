from pydantic import BaseModel, Field

from typing import Optional, Literal

class ActionItem(BaseModel):
    owner: str
    task: str
    deadline: str
    quote: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    review_status: Literal["pending", "accepted", "rejected"] = "pending"

class Decision(BaseModel):
    decision: str
    timestamp: str
    quote: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class Risk(BaseModel):
    description: str
    timestamp: str
    quote: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class MeetingInsights(BaseModel):
    action_items: list[ActionItem]
    decisions: list[Decision]
    risks: list[Risk]
    summary: str
    supporting_context: Optional[list[str]] = None

class TranscriptSegment(BaseModel):
    timestamp: str
    speaker: str
    text: str
