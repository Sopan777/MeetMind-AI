from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/team", tags=["Team"])


@router.get("/members")
def list_members():
    """List team members (mock data)."""
    return [
        {"id": "1", "name": "Alex Chen", "email": "alex@meetingmind.ai", "role": "Admin", "status": "active", "meetings_attended": 42, "tasks_completed": 38},
        {"id": "2", "name": "Sarah Kim", "email": "sarah@meetingmind.ai", "role": "Manager", "status": "active", "meetings_attended": 38, "tasks_completed": 35},
        {"id": "3", "name": "Mike Rodriguez", "email": "mike@meetingmind.ai", "role": "Employee", "status": "active", "meetings_attended": 35, "tasks_completed": 28},
        {"id": "4", "name": "Priya Patel", "email": "priya@meetingmind.ai", "role": "Employee", "status": "away", "meetings_attended": 30, "tasks_completed": 32},
        {"id": "5", "name": "David Park", "email": "david@meetingmind.ai", "role": "Employee", "status": "active", "meetings_attended": 28, "tasks_completed": 22},
        {"id": "6", "name": "Emma Wilson", "email": "emma@meetingmind.ai", "role": "Employee", "status": "offline", "meetings_attended": 25, "tasks_completed": 20},
        {"id": "7", "name": "James Lee", "email": "james@meetingmind.ai", "role": "Viewer", "status": "active", "meetings_attended": 15, "tasks_completed": 12},
        {"id": "8", "name": "Lisa Wang", "email": "lisa@meetingmind.ai", "role": "Manager", "status": "active", "meetings_attended": 33, "tasks_completed": 30},
    ]


@router.post("/invite")
def invite_member(email: str, role: str = "Employee"):
    """Invite a new team member (mock)."""
    return {"message": f"Invitation sent to {email} as {role}", "status": "sent"}
