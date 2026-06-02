import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user

router = APIRouter(prefix="/api/meetings", tags=["Meetings"])


@router.get("/", response_model=list[schemas.MeetingResponse])
def list_meetings(db: Session = Depends(get_db)):
    """List all meetings."""
    return db.query(models.Meeting).order_by(models.Meeting.date.desc()).all()


@router.post("/", response_model=schemas.MeetingResponse, status_code=201)
def create_meeting(data: schemas.MeetingCreate, db: Session = Depends(get_db)):
    """Create a new meeting record."""
    meeting = models.Meeting(
        id=str(uuid.uuid4()),
        title=data.title,
        date=data.date,
        duration=data.duration,
        type=data.type,
        participants=json.dumps(data.participants),
        status="processing",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/{meeting_id}", response_model=schemas.MeetingResponse)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Get a single meeting by ID."""
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/upload")
async def upload_file(meeting_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a meeting recording file."""
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    # In production, save to S3. For now, just record the filename.
    meeting.file_path = file.filename
    db.commit()
    return {"filename": file.filename, "size": file.size, "status": "uploaded"}


@router.get("/{meeting_id}/transcript", response_model=list[schemas.TranscriptResponse])
def get_transcript(meeting_id: str, db: Session = Depends(get_db)):
    """Get transcript entries for a meeting."""
    return db.query(models.Transcript).filter(models.Transcript.meeting_id == meeting_id).all()


@router.get("/{meeting_id}/action-items", response_model=list[schemas.ActionItemResponse])
def get_action_items(meeting_id: str, db: Session = Depends(get_db)):
    """Get action items for a meeting."""
    return db.query(models.ActionItem).filter(models.ActionItem.meeting_id == meeting_id).all()


@router.get("/{meeting_id}/decisions", response_model=list[schemas.DecisionResponse])
def get_decisions(meeting_id: str, db: Session = Depends(get_db)):
    """Get decisions for a meeting."""
    return db.query(models.Decision).filter(models.Decision.meeting_id == meeting_id).all()


@router.get("/{meeting_id}/risks", response_model=list[schemas.RiskResponse])
def get_risks(meeting_id: str, db: Session = Depends(get_db)):
    """Get risks for a meeting."""
    return db.query(models.Risk).filter(models.Risk.meeting_id == meeting_id).all()


@router.get("/{meeting_id}/summary", response_model=schemas.MeetingSummaryResponse)
def get_summary(meeting_id: str):
    """Get AI-generated meeting summary (mock)."""
    return {
        "executive": "The sprint planning session covered Q4 release priorities. Key decisions include migrating to microservices architecture and adopting TypeScript. Three critical risks were identified, with mitigation plans in place. Overall team alignment is strong with 8 action items assigned.",
        "technical": "Technical discussion focused on API integration for the payment gateway using Stripe SDK v3. Frontend will migrate to TypeScript with strict mode. Database schema changes needed for the new analytics module. Performance optimization deferred to Sprint 4. CI/CD pipeline updates required for the new microservices.",
        "client": "The team is making excellent progress on the Q4 release. All core features are on track for the December deadline. We've identified and are actively mitigating potential risks around third-party dependencies. Next check-in scheduled for Wednesday.",
    }


@router.post("/{meeting_id}/process")
def process_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """Trigger AI processing pipeline for a meeting (mock)."""
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.status = "completed"
    meeting.quality_score = 85
    db.commit()
    return {"status": "completed", "message": "AI processing complete"}
