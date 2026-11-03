from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database.base import Base

class Technology(Base):
    __tablename__ = "technologies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # e.g. "Python", "FastAPI", "React", "Docker"
    category = Column(String(50), nullable=True) # "Backend", "Frontend", "Cloud & DevOps", "AI / ML", "Cyber Security", "Database", "Mobile"
    description = Column(String(255), nullable=True)
    icon = Column(String(50), default="code")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class InternRoleTrack(Base):
    __tablename__ = "intern_role_tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True, index=True, nullable=False) # e.g. "Python Backend Intern", "Frontend Web Intern", "Cyber Security Intern"
    domain = Column(String(100), nullable=False) # "Backend", "Frontend", "Cloud/DevOps", "Mobile", "Security", "Data Science", "QA/Testing"
    required_skills_json = Column(Text, default="[]") # JSON list of required technologies
    description = Column(Text, nullable=True)
    duration_months = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
