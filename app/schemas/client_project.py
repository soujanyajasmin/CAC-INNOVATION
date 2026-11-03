from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class ClientBase(BaseModel):
    name: str
    code: str
    industry: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[EmailStr] = None
    tier: Optional[str] = "Enterprise"
    manager_id: Optional[int] = None

class ClientCreate(ClientBase):
    pass

class AssignClientManagerRequest(BaseModel):
    manager_id: int

class ClientOut(ClientBase):
    id: int
    is_active: bool
    manager_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MilestoneBase(BaseModel):
    title: str
    deliverables: Optional[str] = None
    due_date: Optional[datetime] = None
    invoice_amount: Optional[float] = 0.0
    status: Optional[str] = "pending"

class MilestoneCreate(MilestoneBase):
    project_id: int

class MilestoneOut(MilestoneBase):
    id: int
    project_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    project_id: int
    milestone_id: Optional[int] = None
    title: str
    description: str
    assigned_to_id: Optional[int] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "Assigned"
    due_date: Optional[datetime] = None
    repo_url: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskSubmit(BaseModel):
    pr_url: str
    branch_name: Optional[str] = None
    submission_notes: str

class TaskReview(BaseModel):
    status: str # "Approved" or "Changes Requested"
    review_feedback: str

class TaskOut(TaskBase):
    id: int
    created_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    submission_notes: Optional[str] = None
    review_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    client_id: int
    title: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    status: Optional[str] = "in_progress"
    progress_percentage: Optional[int] = 0
    start_date: Optional[datetime] = None
    target_delivery_date: Optional[datetime] = None
    budget: Optional[str] = None
    repo_url: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class DirectProjectCreate(BaseModel):
    title: str
    client_name: str
    manager_id: Optional[int] = None
    tech_stack: List[str] = []
    budget: Optional[str] = "$25,000"
    target_delivery_date: Optional[datetime] = None
    description: Optional[str] = None
    repo_url: Optional[str] = None

class ProjectOut(ProjectBase):
    id: int
    milestones: List[MilestoneOut] = []
    tasks: List[TaskOut] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConvertLeadRequest(BaseModel):
    lead_id: int
    project_title: str
    manager_id: Optional[int] = None
    budget: Optional[str] = None
    target_delivery_date: Optional[datetime] = None

class InvoiceCreate(BaseModel):
    client_id: int
    project_id: Optional[int] = None
    milestone_id: Optional[int] = None
    amount: float
    invoice_number: str
    due_date: Optional[datetime] = None

class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    client_id: int
    project_id: Optional[int] = None
    amount: float
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    notification_type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SupportTicketCreate(BaseModel):
    subject: str
    category: Optional[str] = "Technical Support"
    priority: Optional[str] = "Medium"
    initial_message: str

class SupportTicketOut(BaseModel):
    id: int
    client_id: int
    user_id: int
    assigned_employee_id: Optional[int] = None
    subject: str
    category: str
    priority: str
    status: str
    messages_json: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
