import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=list[schemas.ActionItemResponse])
def list_tasks(db: Session = Depends(get_db)):
    """List all action items (tasks)."""
    return db.query(models.ActionItem).all()


@router.post("/", response_model=schemas.ActionItemResponse, status_code=201)
def create_task(data: schemas.ActionItemCreate, db: Session = Depends(get_db)):
    """Create a task manually."""
    item = models.ActionItem(
        id=str(uuid.uuid4()),
        meeting_id=data.meeting_id,
        task=data.task,
        owner=data.owner,
        deadline=data.deadline,
        priority=data.priority,
        status="todo",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{task_id}", response_model=schemas.ActionItemResponse)
def update_task(task_id: str, data: schemas.ActionItemUpdate, db: Session = Depends(get_db)):
    """Update task status, priority, or owner."""
    task = db.query(models.ActionItem).filter(models.ActionItem.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if data.status is not None:
        task.status = data.status
    if data.priority is not None:
        task.priority = data.priority
    if data.owner is not None:
        task.owner = data.owner
    db.commit()
    db.refresh(task)
    return task
