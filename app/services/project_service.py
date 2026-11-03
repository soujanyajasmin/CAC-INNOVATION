import re
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.content import Enquiry
from app.models.client_project import Client, Project, Milestone, Task, Notification, Invoice
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.client_project import ConvertLeadRequest, TaskCreate, TaskSubmit, TaskReview

class ProjectWorkflowService:
    @staticmethod
    def create_notification(db: Session, user_id: int, title: str, message: str, link: Optional[str] = None, n_type: str = "general") -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            notification_type=n_type
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @classmethod
    def convert_lead_to_client_and_project(cls, db: Session, req: ConvertLeadRequest, creator_user: User) -> Project:
        lead = db.query(Enquiry).filter(Enquiry.id == req.lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        # 1. Generate client code from company name or lead name
        raw_code = (lead.company or lead.name).strip().upper()
        clean_code = re.sub(r'[^A-Z0-9]', '', raw_code)[:12] or "CLIENT"
        code = f"{clean_code}-{lead.id}"

        # 2. Find or create client record
        client = db.query(Client).filter(
            (Client.code == code) | (Client.primary_contact_email == lead.email)
        ).first()
        if not client:
            client = Client(
                name=lead.company or f"{lead.name} Client",
                code=code,
                industry=lead.industry or "Technology",
                primary_contact_name=lead.name,
                primary_contact_email=lead.email,
                tier="Standard Enterprise",
                manager_id=req.manager_id
            )
            db.add(client)
            db.commit()
            db.refresh(client)
        elif req.manager_id and not client.manager_id:
            client.manager_id = req.manager_id
            db.commit()

        # 3. Create project record assigned to manager
        project = Project(
            client_id=client.id,
            manager_id=req.manager_id,
            title=req.project_title,
            description=lead.message,
            budget=req.budget or lead.budget,
            target_delivery_date=req.target_delivery_date,
            status="planning",
            progress_percentage=0
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # 4. Create default milestone 1
        m1 = Milestone(
            project_id=project.id,
            title="Phase 1: Architecture Blueprint & Requirements Specification",
            deliverables="Technical requirement specification, API contract, and repo initialization.",
            status="in_progress"
        )
        db.add(m1)

        # 5. Update lead status to won and link IDs
        lead.status = "won"
        lead.converted_client_id = client.id
        lead.converted_project_id = project.id
        db.commit()

        # 6. Notify Manager if assigned
        if req.manager_id:
            cls.create_notification(
                db=db,
                user_id=req.manager_id,
                title="New Project Assigned",
                message=f"You have been assigned as Project Manager for '{project.title}' ({client.name}).",
                link=f"/manager#project-{project.id}",
                n_type="project_assignment"
            )

        # Audit log
        audit = AuditLog(
            user_id=creator_user.id,
            user_email=creator_user.email,
            action="LEAD_CONVERTED_TO_PROJECT",
            entity="project",
            entity_id=str(project.id),
            details=f"Lead #{lead.id} converted into Client '{client.name}' and Project '{project.title}'"
        )
        db.add(audit)
        db.commit()

        return project

    @classmethod
    def assign_client_manager(cls, db: Session, client_id: int, manager_id: int, current_user: User) -> Client:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Client #{client_id} not found")
        
        manager = db.query(User).filter(User.id == manager_id).first()
        if not manager:
            raise ValueError(f"Manager #{manager_id} not found")
        if manager.role.name not in ["manager", "admin", "super_admin"]:
            raise ValueError(f"User '{manager.full_name}' is not a Manager")

        client.manager_id = manager.id
        
        # Also assign manager to client's existing projects if unassigned
        for p in client.projects:
            if not p.manager_id:
                p.manager_id = manager.id

        db.commit()
        db.refresh(client)

        # Notify Manager
        cls.create_notification(
            db=db,
            user_id=manager.id,
            title="Client Account Assigned",
            message=f"Admin assigned you as Account Manager for client '{client.name}'.",
            link=f"/manager#client-{client.id}",
            n_type="client_assignment"
        )

        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            user_email=current_user.email,
            action="CLIENT_ASSIGNED_TO_MANAGER",
            entity="client",
            entity_id=str(client.id),
            details=f"Admin {current_user.full_name} assigned Client '{client.name}' to Manager '{manager.full_name}' ({manager.email})"
        )
        db.add(audit)
        db.commit()

        return client

    @classmethod
    def assign_task(cls, db: Session, task_in: TaskCreate, creator_user: User) -> Task:
        task = Task(
            project_id=task_in.project_id,
            milestone_id=task_in.milestone_id,
            title=task_in.title,
            description=task_in.description,
            assigned_to_id=task_in.assigned_to_id,
            created_by_id=creator_user.id,
            priority=task_in.priority or "Medium",
            status="Assigned",
            due_date=task_in.due_date,
            repo_url=task_in.repo_url
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Notify assigned user (employee or intern)
        if task_in.assigned_to_id:
            cls.create_notification(
                db=db,
                user_id=task_in.assigned_to_id,
                title="New Task Assigned",
                message=f"Task '{task.title}' has been assigned to you. Priority: {task.priority}.",
                link=f"/portal#task-{task.id}",
                n_type="task_assignment"
            )

        return task

    @classmethod
    def submit_task_work(cls, db: Session, task_id: int, sub: TaskSubmit, submitter: User) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")

        task.pr_url = sub.pr_url
        task.branch_name = sub.branch_name
        task.submission_notes = sub.submission_notes
        task.status = "Under Review"
        db.commit()
        db.refresh(task)

        # Notify project manager or task creator for review
        reviewer_id = task.created_by_id or (task.project.manager_id if task.project else None)
        if reviewer_id:
            cls.create_notification(
                db=db,
                user_id=reviewer_id,
                title="Task Ready for Review",
                message=f"{submitter.full_name} submitted work for task '{task.title}' with PR: {sub.pr_url}",
                link=f"/manager#task-{task.id}",
                n_type="task_submitted"
            )

        return task

    @classmethod
    def review_task(cls, db: Session, task_id: int, review: TaskReview, reviewer: User) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")

        task.review_feedback = review.review_feedback
        if review.status.lower() in ["approved", "completed"]:
            task.status = "Approved"
            task.approved_by_id = reviewer.id
        else:
            task.status = "Changes Requested"

        db.commit()
        db.refresh(task)

        # Recalculate project progress
        cls.update_project_progress(db, task.project_id)

        # Notify assignee
        if task.assigned_to_id:
            cls.create_notification(
                db=db,
                user_id=task.assigned_to_id,
                title=f"Task {task.status}",
                message=f"Review by {reviewer.full_name}: {review.review_feedback}",
                link=f"/portal#task-{task.id}",
                n_type="review_feedback"
            )

        return task

    @staticmethod
    def update_project_progress(db: Session, project_id: int):
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        if not tasks:
            return
        completed = sum(1 for t in tasks if t.status in ["Approved", "Completed"])
        pct = int((completed / len(tasks)) * 100)
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            proj.progress_percentage = pct
            if pct == 100:
                proj.status = "review"
            db.commit()
