from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False) 
    # super_admin, admin, manager, employee, intern, client
    description = Column(String(255))
    permissions = Column(Text, default="[]") # JSON list of permission strings

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=True) # e.g. "Senior AI Engineer", "Project Lead"
    department = Column(String(100), nullable=True) # "Engineering", "Business Dev", "Product"
    skills_json = Column(Text, default="[]") # JSON list of skills
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("clients.id"), nullable=True) # For clients
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    role = relationship("Role", back_populates="users")
    client = relationship("Client", back_populates="users", foreign_keys=[tenant_id])
    submissions = relationship("InternSubmission", back_populates="intern", foreign_keys="InternSubmission.intern_id")
    support_tickets = relationship("SupportTicket", back_populates="user", foreign_keys="SupportTicket.user_id")
    assigned_tasks = relationship("Task", back_populates="assigned_to", foreign_keys="Task.assigned_to_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
