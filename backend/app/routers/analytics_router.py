from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=schemas.AnalyticsOverview)
def get_overview(db: Session = Depends(get_db)):
    """Get dashboard analytics overview."""
    total_meetings = db.query(models.Meeting).count()
    total_actions = db.query(models.ActionItem).count()
    total_decisions = db.query(models.Decision).count()
    total_risks = db.query(models.Risk).count()
    total_duration = db.query(func.sum(models.Meeting.duration)).scalar() or 0
    return {
        "total_meetings": total_meetings,
        "total_action_items": total_actions,
        "total_decisions": total_decisions,
        "total_risks": total_risks,
        "hours_saved": round(total_duration * 0.3 / 60, 1),
    }


@router.get("/charts")
def get_chart_data():
    """Get data for analytics charts (mock)."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return {
        "meeting_counts": [{"month": m, "count": c} for m, c in zip(months, [12, 15, 18, 22, 20, 25, 28, 30, 32, 35, 38, 42])],
        "sentiment_trend": [{"month": m, "positive": p, "neutral": n, "negative": ne} for m, p, n, ne in zip(months, [60,62,58,65,68,70,72,75,73,78,80,82], [25,24,28,22,20,18,17,15,17,14,12,11], [15,14,14,13,12,12,11,10,10,8,8,7])],
        "risk_trend": [{"month": m, "low": l, "medium": me, "high": h, "critical": c} for m, l, me, h, c in zip(months, [5,6,4,7,5,6,8,5,4,6,5,4], [3,4,3,5,4,3,4,3,2,3,3,2], [2,1,2,2,1,2,1,1,1,1,0,1], [0,1,0,1,0,0,1,0,0,0,0,0])],
        "task_completion": [
            {"status": "Completed", "count": 85, "color": "#10B981"},
            {"status": "In Progress", "count": 32, "color": "#6366F1"},
            {"status": "Review", "count": 18, "color": "#8B5CF6"},
            {"status": "To Do", "count": 25, "color": "#64748B"},
        ],
        "decision_frequency": [{"month": m, "decisions": d} for m, d in zip(months, [8,10,12,15,13,16,18,20,19,22,24,26])],
    }


@router.get("/quality-score")
def get_quality_score():
    """Get meeting quality score breakdown (mock)."""
    return {
        "overall": 85,
        "metrics": {
            "participation_balance": 82,
            "action_clarity": 91,
            "decision_quality": 78,
            "risk_awareness": 85,
            "overall_productivity": 88,
        },
        "recommendation": "Consider allocating more time for risk discussion in future meetings. Action items could benefit from clearer ownership assignments.",
    }
