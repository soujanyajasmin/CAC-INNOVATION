import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import get_current_user, require_admin, require_manager, require_employee
from app.models.client_project import Project, Milestone, Task, SupportTicket, Client, Notification, Invoice
from app.models.user import User
from app.schemas.client_project import (
    ProjectCreate, ProjectOut, MilestoneCreate, MilestoneOut,
    TaskCreate, TaskOut, TaskSubmit, TaskReview,
    ConvertLeadRequest, SupportTicketCreate, SupportTicketOut,
    NotificationOut, InvoiceOut, DirectProjectCreate,
    ClientOut, AssignClientManagerRequest
)
from app.services.project_service import ProjectWorkflowService

router = APIRouter(prefix="/projects", tags=["Projects & Tasks Operations"])

@router.get("/", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.name == "client":
        if not current_user.tenant_id:
            return []
        return db.query(Project).filter(Project.client_id == current_user.tenant_id).all()
    elif current_user.role.name == "manager":
        return db.query(Project).filter((Project.manager_id == current_user.id) | (Project.manager_id == None)).all()
    return db.query(Project).all()

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    proj_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    project = Project(**proj_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.post("/clients/{client_id}/assign-manager", response_model=ClientOut)
def assign_client_manager_endpoint(
    client_id: int,
    req: AssignClientManagerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Assign a Client to a designated Account Manager"""
    try:
        client = ProjectWorkflowService.assign_client_manager(db, client_id, req.manager_id, current_user)
        return ClientOut(
            id=client.id,
            name=client.name,
            code=client.code,
            industry=client.industry,
            primary_contact_name=client.primary_contact_name,
            primary_contact_email=client.primary_contact_email,
            tier=client.tier,
            manager_id=client.manager_id,
            manager_name=client.manager.full_name if client.manager else None,
            is_active=client.is_active,
            created_at=client.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/convert-lead", response_model=ProjectOut)
def convert_lead_to_project(
    req: ConvertLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    try:
        project = ProjectWorkflowService.convert_lead_to_client_and_project(db, req, current_user)
        return project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/direct", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project_direct(
    req: DirectProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Directly create a new project workspace with client & tech stack"""
    client_name = req.client_name.strip()
    client = db.query(Client).filter(Client.name.ilike(client_name)).first()
    if not client:
        clean_code = re.sub(r'[^A-Z0-9]', '', client_name.upper())[:10]
        code = f"{clean_code}-{db.query(Client).count() + 1}"
        client = Client(
            name=client_name,
            code=code,
            industry="Technology",
            tier="Standard",
            manager_id=req.manager_id
        )
        db.add(client)
        db.commit()
        db.refresh(client)
    elif req.manager_id and not client.manager_id:
        client.manager_id = req.manager_id
        db.commit()

    project = Project(
        client_id=client.id,
        manager_id=req.manager_id,
        title=req.title.strip(),
        description=req.description.strip() if req.description else None,
        budget=req.budget,
        tech_stack_json=json.dumps(req.tech_stack) if req.tech_stack else '["FastAPI", "Python"]',
        target_delivery_date=req.target_delivery_date,
        repo_url=req.repo_url,
        status="in_progress",
        progress_percentage=0
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Automatically create Phase 1 initialization milestone
    m1 = Milestone(
        project_id=project.id,
        title="Phase 1: Architecture, Data Schema & Setup",
        deliverables="Architecture specification & repository setup",
        status="in_progress"
    )
    db.add(m1)
    db.commit()
    db.refresh(project)

    return project

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role.name == "client" and current_user.tenant_id != project.client_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this project")
    return project

# Milestones
@router.post("/{project_id}/milestones", response_model=MilestoneOut)
def add_milestone(
    project_id: int,
    milestone_in: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    milestone = Milestone(**milestone_in.model_dump())
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone

# Tasks Workflow
@router.post("/tasks", response_model=TaskOut)
def assign_new_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee) # Manager or Senior Dev can create task
):
    return ProjectWorkflowService.assign_task(db, task_in, current_user)

@router.get("/tasks/my", response_model=List[TaskOut])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Task).filter(Task.assigned_to_id == current_user.id).order_by(Task.due_date.asc()).all()

@router.post("/tasks/{task_id}/submit", response_model=TaskOut)
def submit_task(
    task_id: int,
    sub_in: TaskSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ProjectWorkflowService.submit_task_work(db, task_id, sub_in, current_user)

@router.post("/tasks/{task_id}/review", response_model=TaskOut)
def review_task(
    task_id: int,
    review_in: TaskReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    return ProjectWorkflowService.review_task(db, task_id, review_in, current_user)

# Notifications
@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(20).all()

@router.patch("/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"success": True}

# Support Tickets
@router.post("/tickets", response_model=SupportTicketOut)
def create_support_ticket(
    ticket_in: SupportTicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client_id = current_user.tenant_id
    if not client_id:
        first_c = db.query(Client).first()
        client_id = first_c.id if first_c else 1

    initial_messages = [{
        "sender": current_user.full_name,
        "message": ticket_in.initial_message,
        "timestamp": "Just now"
    }]

    ticket = SupportTicket(
        client_id=client_id,
        user_id=current_user.id,
        subject=ticket_in.subject,
        category=ticket_in.category,
        priority=ticket_in.priority,
        messages_json=json.dumps(initial_messages)
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/tickets/my", response_model=List[SupportTicketOut])
def get_user_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.name == "client":
        return db.query(SupportTicket).filter(SupportTicket.client_id == current_user.tenant_id).all()
    return db.query(SupportTicket).all()
