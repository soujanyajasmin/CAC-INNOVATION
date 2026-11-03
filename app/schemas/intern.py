from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class InternBatchBase(BaseModel):
    batch_name: str
    track: str
    start_date: datetime
    end_date: datetime
    mentor_name: Optional[str] = "Technical Lead"
    is_active: Optional[bool] = True

class InternBatchCreate(InternBatchBase):
    pass

class InternTaskBase(BaseModel):
    batch_id: int
    title: str
    track: Optional[str] = None
    description: str
    acceptance_criteria: str
    due_date: Optional[datetime] = None
    difficulty: Optional[str] = "Intermediate"

class InternTaskCreate(InternTaskBase):
    pass

class InternSubmissionCreate(BaseModel):
    task_id: int
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None
    notes: Optional[str] = None

class InternSubmissionReview(BaseModel):
    status: str # approved, revision_requested, rejected
    score: int
    mentor_feedback: str

class InternSubmissionOut(BaseModel):
    id: int
    task_id: int
    intern_id: int
    repo_url: Optional[str] = None
    demo_url: Optional[str] = None
    notes: Optional[str] = None
    status: str
    score: Optional[int] = None
    mentor_feedback: Optional[str] = None
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InternTaskOut(InternTaskBase):
    id: int
    submissions: List[InternSubmissionOut] = []
    model_config = ConfigDict(from_attributes=True)

class InternBatchOut(InternBatchBase):
    id: int
    tasks: List[InternTaskOut] = []
    model_config = ConfigDict(from_attributes=True)
