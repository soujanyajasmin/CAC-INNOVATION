from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from app.database.base import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(150), nullable=False)
    short_description = Column(String(300), nullable=False)
    full_description = Column(Text, nullable=False)
    icon = Column(String(50), default="cpu")
    deliverables = Column(Text, default="[]")
    example_outcome = Column(String(255), nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Industry(Base):
    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), default="briefcase")
    summary = Column(Text, nullable=False)
    solutions_json = Column(Text, default="[]")
    considerations_json = Column(Text, default="[]")
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class PortfolioProject(Base):
    __tablename__ = "portfolio_projects"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    client_name = Column(String(100), default="Enterprise Partner")
    industry_name = Column(String(100), nullable=False)
    challenge = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    tech_stack_json = Column(Text, default="[]")
    outcomes_json = Column(Text, default="[]")
    image_url = Column(String(255), nullable=True)
    is_featured = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False, index=True)
    company = Column(String(150), nullable=True)
    industry = Column(String(100), nullable=True)
    service_interest = Column(String(100), nullable=True)
    budget = Column(String(50), nullable=True)
    timeline = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    
    # CRM Pipeline Stage
    # new_enquiry, contacted, requirement_discussion, proposal_sent, negotiation, won, lost
    status = Column(String(30), default="new_enquiry")
    assigned_to = Column(String(100), nullable=True) # Lead Owner (Admin / BD)
    lead_score = Column(Integer, default=50) # Auto-scored by qualification agent
    qualification_notes = Column(Text, nullable=True)
    
    # Conversion tracking
    converted_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    converted_project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
