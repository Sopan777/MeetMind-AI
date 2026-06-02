from pydantic import BaseModel


class ActionItem(BaseModel):
    owner: str
    task: str
    deadline: str


class Decision(BaseModel):
    decision: str
    timestamp: str


class Risk(BaseModel):
    description: str
    timestamp: str


class MeetingInsights(BaseModel):
    action_items: list[ActionItem]
    decisions: list[Decision]
    risks: list[Risk]
    summary: str


class TranscriptSegment(BaseModel):
    timestamp: str
    speaker: str
    text: str
