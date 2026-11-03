from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.base import Base

class InternBatch(Base):
    __tablename__ = "intern_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String(100), nullable=False) # e.g. "Cohort 2026 - AI Engineering"
    track = Column(String(100), nullable=False) # Full-Stack AI, Computer Vision, GenAI & RAG, ML Ops
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    mentor_name = Column(String(100), default="Technical Lead")
    is_active = Column(Boolean, default=True)

    tasks = relationship("InternTask", back_populates="batch", cascade="all, delete-orphan")

class InternTask(Base):
    __tablename__ = "intern_tasks"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("intern_batches.id"), nullable=False)
    title = Column(String(200), nullable=False)
    track = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    acceptance_criteria = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    difficulty = Column(String(30), default="Intermediate")

    batch = relationship("InternBatch", back_populates="tasks")
    submissions = relationship("InternSubmission", back_populates="task", cascade="all, delete-orphan")

class InternSubmission(Base):
    __tablename__ = "intern_submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("intern_tasks.id"), nullable=False)
    intern_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repo_url = Column(String(255), nullable=True)
    demo_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="submitted") # submitted, under_review, approved, revision_requested
    score = Column(Integer, nullable=True) # 0 to 100
    mentor_feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("InternTask", back_populates="submissions")
    intern = relationship("User", back_populates="submissions", foreign_keys=[intern_id])
