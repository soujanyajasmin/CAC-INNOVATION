from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import get_current_user, require_trainer
from app.models.intern import InternBatch, InternTask, InternSubmission
from app.models.user import User
from app.schemas.intern import (
    InternBatchCreate, InternBatchOut, InternTaskCreate, InternTaskOut,
    InternSubmissionCreate, InternSubmissionReview, InternSubmissionOut
)

router = APIRouter(prefix="/interns", tags=["Research, Training & Internships"])

@router.get("/batches", response_model=List[InternBatchOut])
def list_batches(db: Session = Depends(get_db)):
    return db.query(InternBatch).filter(InternBatch.is_active == True).all()

@router.post("/batches", response_model=InternBatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    batch_in: InternBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_trainer)
):
    batch = InternBatch(**batch_in.model_dump())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

@router.get("/tasks", response_model=List[InternTaskOut])
def list_tasks(
    batch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InternTask)
    if batch_id:
        query = query.filter(InternTask.batch_id == batch_id)
    return query.all()

@router.post("/tasks", response_model=InternTaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: InternTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_trainer)
):
    task = InternTask(**task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.post("/submissions", response_model=InternSubmissionOut)
def submit_task(
    sub_in: InternSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if existing submission
    existing = db.query(InternSubmission).filter(
        InternSubmission.task_id == sub_in.task_id,
        InternSubmission.intern_id == current_user.id
    ).first()
    
    if existing:
        existing.repo_url = sub_in.repo_url
        existing.demo_url = sub_in.demo_url
        existing.notes = sub_in.notes
        existing.status = "resubmitted"
        db.commit()
        db.refresh(existing)
        return existing

    sub = InternSubmission(
        task_id=sub_in.task_id,
        intern_id=current_user.id,
        repo_url=sub_in.repo_url,
        demo_url=sub_in.demo_url,
        notes=sub_in.notes,
        status="submitted"
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@router.post("/submissions/{sub_id}/review", response_model=InternSubmissionOut)
def review_submission(
    sub_id: int,
    review_in: InternSubmissionReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_trainer)
):
    sub = db.query(InternSubmission).filter(InternSubmission.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.status = review_in.status
    sub.score = review_in.score
    sub.mentor_feedback = review_in.mentor_feedback
    db.commit()
    db.refresh(sub)
    return sub
