from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# Service Schemas
class ServiceBase(BaseModel):
    slug: str
    title: str
    short_description: str
    full_description: str
    icon: Optional[str] = "cpu"
    deliverables: Optional[str] = "[]"
    example_outcome: Optional[str] = None
    display_order: Optional[int] = 0
    is_active: Optional[bool] = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    icon: Optional[str] = None
    deliverables: Optional[str] = None
    example_outcome: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class ServiceOut(ServiceBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Industry Schemas
class IndustryBase(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = "briefcase"
    summary: str
    solutions_json: Optional[str] = "[]"
    considerations_json: Optional[str] = "[]"
    display_order: Optional[int] = 0
    is_active: Optional[bool] = True

class IndustryCreate(IndustryBase):
    pass

class IndustryOut(IndustryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Portfolio Schemas
class PortfolioBase(BaseModel):
    slug: str
    title: str
    client_name: Optional[str] = "Enterprise Partner"
    industry_name: str
    challenge: str
    solution: str
    tech_stack_json: Optional[str] = "[]"
    outcomes_json: Optional[str] = "[]"
    image_url: Optional[str] = None
    is_featured: Optional[bool] = True

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioOut(PortfolioBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Enquiry Schemas
class EnquiryCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    industry: Optional[str] = None
    service_interest: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    message: str

class EnquiryUpdateStatus(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    qualification_notes: Optional[str] = None

class EnquiryOut(BaseModel):
    id: int
    name: str
    email: str
    company: Optional[str] = None
    industry: Optional[str] = None
    service_interest: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    message: str
    status: str
    assigned_to: Optional[str] = None
    lead_score: int
    qualification_notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
