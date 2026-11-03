from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.base import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    industry = Column(String(100), nullable=True)
    primary_contact_name = Column(String(100), nullable=True)
    primary_contact_email = Column(String(120), nullable=True)
    tier = Column(String(50), default="Enterprise")
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Assigned Manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    manager = relationship("User", foreign_keys=[manager_id])
    users = relationship("User", back_populates="client", foreign_keys="User.tenant_id")
    projects = relationship("Project", back_populates="client")
    tickets = relationship("SupportTicket", back_populates="client")
    knowledge_bases = relationship("KnowledgeBase", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Assigned Manager
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="in_progress") # planning, in_progress, review, completed, maintenance
    progress_percentage = Column(Integer, default=0)
    start_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    target_delivery_date = Column(DateTime, nullable=True)
    budget = Column(String(50), nullable=True)
    tech_stack_json = Column(Text, default='["FastAPI", "SQLite/PostgreSQL", "PyTorch"]')
    repo_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="projects")
    manager = relationship("User", foreign_keys=[manager_id])
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="project")

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(150), nullable=False)
    deliverables = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    invoice_amount = Column(Float, default=0.0)
    status = Column(String(50), default="pending") # pending, in_review, approved, completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="milestones")
    tasks = relationship("Task", back_populates="milestone")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Employee or Intern
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Manager or Senior Dev
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Approving Manager
    
    # Priority: Critical, High, Medium, Low
    priority = Column(String(20), default="Medium")
    
    # Status: Backlog, Assigned, In Progress, Under Review, Changes Requested, Approved, Completed
    status = Column(String(30), default="Assigned")
    due_date = Column(DateTime, nullable=True)
    
    # GitHub & Development Tracking
    repo_url = Column(String(255), nullable=True)
    branch_name = Column(String(100), nullable=True)
    pr_url = Column(String(255), nullable=True)
    submission_notes = Column(Text, nullable=True)
    review_feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tasks")
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")

class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="comments")
    user = relationship("User")

class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), nullable=False)
    file_path = Column(String(255), nullable=True)
    doc_type = Column(String(50), default="Architecture") # Requirements, Architecture, Dataset, Report, Deliverable
    version = Column(String(20), default="v1.0")
    access_level = Column(String(30), default="all") # client_approved, internal_only, manager_admin_only
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="documents")
    uploaded_by = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50), default="task_assignment") # task_assignment, task_submitted, review_approved, changes_requested, lead_created
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False) # e.g. INV-2026-001
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String(30), default="sent") # draft, sent, paid, overdue
    payment_method = Column(String(50), default="Bank Wire / Razorpay")
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="invoices")
    project = relationship("Project", back_populates="invoices")
    milestone = relationship("Milestone")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_employee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject = Column(String(200), nullable=False)
    category = Column(String(50), default="Technical Support") # Bug, Feature Request, Billing, AI Tuning
    priority = Column(String(20), default="Medium") # Low, Medium, High, Urgent
    status = Column(String(30), default="Open") # Open, Assigned, In Progress, Waiting for Client, Resolved, Closed
    messages_json = Column(Text, default="[]") # Conversation trail
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="tickets")
    user = relationship("User", foreign_keys=[user_id], back_populates="support_tickets")
    assigned_employee = relationship("User", foreign_keys=[assigned_employee_id])
