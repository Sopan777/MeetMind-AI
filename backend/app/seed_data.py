"""Seed the database with demo data matching the frontend's mock-data.ts."""
import json
from sqlalchemy.orm import Session
from . import models
from .auth import hash_password


def seed_database(db: Session):
    """Populate DB with realistic demo data if empty."""
    if db.query(models.User).first():
        return  # Already seeded

    # Demo user
    user = models.User(
        id="user-1",
        name="Alex Chen",
        email="alex@meetingmind.ai",
        hashed_password=hash_password("password123"),
        role="Admin",
    )
    db.add(user)

    # Meetings
    meetings_data = [
        ("meeting-1", "Sprint Planning - Q4 Release", "2024-12-10", 75, "completed", "sprint-planning", 88, ["Alex Chen", "Sarah Kim", "Mike Rodriguez", "Priya Patel"]),
        ("meeting-2", "Client Onboarding - Acme Corp", "2024-12-09", 45, "completed", "client-call", 82, ["Alex Chen", "Emma Wilson", "David Park"]),
        ("meeting-3", "Weekly Standup - Engineering", "2024-12-08", 15, "completed", "standup", 75, ["Alex Chen", "Sarah Kim", "Mike Rodriguez", "Priya Patel", "David Park"]),
        ("meeting-4", "Q4 Budget Review", "2024-12-07", 60, "completed", "all-hands", 90, ["Alex Chen", "Lisa Wang", "James Lee"]),
        ("meeting-5", "Product Roadmap Discussion", "2024-12-06", 90, "completed", "sprint-planning", 85, ["Alex Chen", "Sarah Kim", "Emma Wilson"]),
        ("meeting-6", "Design System Workshop", "2024-12-05", 45, "completed", "retrospective", 78, ["Sarah Kim", "David Park", "Emma Wilson"]),
        ("meeting-7", "Security Audit Follow-up", "2024-12-04", 30, "processing", "one-on-one", 0, ["Alex Chen", "Mike Rodriguez"]),
        ("meeting-8", "All-Hands Meeting - December", "2024-12-03", 60, "completed", "all-hands", 92, ["Alex Chen", "Sarah Kim", "Mike Rodriguez", "Priya Patel", "David Park", "Emma Wilson", "James Lee", "Lisa Wang"]),
    ]
    for mid, title, date, dur, status, mtype, score, parts in meetings_data:
        db.add(models.Meeting(id=mid, title=title, date=date, duration=dur, status=status, type=mtype, quality_score=score, participants=json.dumps(parts), user_id="user-1"))

    # Transcript for meeting-1
    transcript_data = [
        ("t1", "Alex Chen", "00:00:12", "Alright everyone, let's kick off our sprint planning for the Q4 release."),
        ("t2", "Alex Chen", "00:00:30", "First, let's review what we accomplished last sprint and any carry-overs."),
        ("t3", "Sarah Kim", "00:01:15", "The frontend redesign is about 80% complete. We still need to finalize the dashboard components."),
        ("t4", "Mike Rodriguez", "00:02:00", "I've been working on the API integration for the payment gateway. We're blocked by the third-party SDK issue."),
        ("t5", "Priya Patel", "00:02:45", "The authentication flow redesign is done. I'll need someone to review the PR."),
        ("t6", "Alex Chen", "00:03:30", "Great progress. Mike, what's the timeline for resolving the SDK issue?"),
        ("t7", "Mike Rodriguez", "00:04:00", "I've reached out to their support team. Expecting a fix by end of week. This is our biggest blocker right now."),
        ("t8", "Sarah Kim", "00:05:15", "For the dashboard, I recommend we adopt TypeScript for all new components going forward."),
        ("t9", "Alex Chen", "00:06:00", "That's a good idea. Let's make that a team decision. All in favor? Great, TypeScript it is."),
        ("t10", "Priya Patel", "00:07:30", "We should also consider the deployment timeline. The current CI/CD pipeline needs updates for microservices."),
    ]
    for tid, speaker, ts, text in transcript_data:
        db.add(models.Transcript(id=tid, meeting_id="meeting-1", speaker=speaker, timestamp=ts, text=text))

    # Action Items
    action_items = [
        ("ai-1", "meeting-1", "Complete API integration for payment gateway", "Mike Rodriguez", "2024-12-20", "in-progress", "critical"),
        ("ai-2", "meeting-1", "Update design system documentation", "Sarah Kim", "2024-12-18", "todo", "high"),
        ("ai-3", "meeting-1", "Fix authentication flow bug on mobile", "Priya Patel", "2024-12-15", "review", "high"),
        ("ai-4", "meeting-1", "Set up TypeScript strict mode for frontend", "Sarah Kim", "2024-12-22", "todo", "medium"),
        ("ai-5", "meeting-2", "Prepare client onboarding materials", "Emma Wilson", "2024-12-16", "completed", "medium"),
        ("ai-6", "meeting-2", "Schedule follow-up demo with Acme Corp", "David Park", "2024-12-19", "in-progress", "high"),
        ("ai-7", "meeting-3", "Deploy hotfix for production API", "Mike Rodriguez", "2024-12-09", "completed", "critical"),
        ("ai-8", "meeting-4", "Submit revised Q4 budget proposal", "Lisa Wang", "2024-12-14", "review", "high"),
        ("ai-9", "meeting-5", "Create product roadmap presentation", "Alex Chen", "2024-12-21", "in-progress", "medium"),
        ("ai-10", "meeting-6", "Build reusable component library", "David Park", "2024-12-25", "todo", "medium"),
    ]
    for aid, mid, task, owner, deadline, status, priority in action_items:
        db.add(models.ActionItem(id=aid, meeting_id=mid, task=task, owner=owner, deadline=deadline, status=status, priority=priority))

    # Decisions
    decisions_data = [
        ("d-1", "meeting-1", "Migrate to microservices architecture", "Team agreed to break the monolith into microservices for the payment module.", "Alex Chen", "high"),
        ("d-2", "meeting-1", "Adopt TypeScript for all new frontend code", "All new components and features will use TypeScript with strict mode.", "Sarah Kim", "medium"),
        ("d-3", "meeting-4", "Delay Q4 launch by 2 weeks", "Additional time needed for security audit and performance testing.", "Alex Chen", "high"),
        ("d-4", "meeting-5", "Prioritize mobile experience for Q1", "Mobile-first approach for all new features in Q1 2025.", "Alex Chen", "medium"),
    ]
    for did, mid, title, desc, decidedBy, impact in decisions_data:
        db.add(models.Decision(id=did, meeting_id=mid, title=title, description=desc, decided_by=decidedBy, impact=impact))

    # Risks
    risks_data = [
        ("r-1", "meeting-1", "API integration delayed", "Third-party payment SDK has unresolved bugs.", "high", "May delay Q4 release by 1-2 weeks", "Explore alternative payment providers as backup", "blocked"),
        ("r-2", "meeting-1", "Resource constraint for testing", "QA team is understaffed for the security audit.", "medium", "Could miss critical security vulnerabilities", "Hire contract QA engineers for December", "resource issue"),
        ("r-3", "meeting-4", "Budget overrun risk", "Q4 marketing spend exceeding projections.", "high", "May need to cut features or delay campaigns", "Review and prioritize marketing initiatives", "budget issue"),
        ("r-4", "meeting-7", "Authentication vulnerability", "Potential session fixation issue identified.", "critical", "Security breach risk for user accounts", "Immediate patch and security audit", "waiting for approval"),
    ]
    for rid, mid, title, desc, severity, impact, rec, phrase in risks_data:
        db.add(models.Risk(id=rid, meeting_id=mid, title=title, description=desc, severity=severity, impact=impact, recommendation=rec, detected_phrase=phrase))

    # Notifications
    notifs = [
        ("n-1", "meeting-processed", "Meeting Processed", "Sprint Planning - Q4 Release has been processed.", False),
        ("n-2", "risk-detected", "New Risk Detected", "High severity risk identified in Q4 Budget Review.", False),
        ("n-3", "action-assigned", "Action Item Assigned", "You have been assigned: Complete API integration.", True),
        ("n-4", "deadline-approaching", "Deadline Approaching", "Fix authentication flow bug is due in 2 days.", False),
    ]
    for nid, ntype, title, msg, read in notifs:
        db.add(models.Notification(id=nid, user_id="user-1", type=ntype, title=title, message=msg, read=read))

    db.commit()
