from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class TechnologyBase(BaseModel):
    name: str
    category: Optional[str] = "Backend"
    description: Optional[str] = None
    icon: Optional[str] = "code"

class TechnologyCreate(TechnologyBase):
    pass

class TechnologyOut(TechnologyBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InternRoleTrackBase(BaseModel):
    title: str
    domain: str
    required_skills: List[str] = []
    description: Optional[str] = None
    duration_months: Optional[int] = 3

class InternRoleTrackCreate(InternRoleTrackBase):
    pass

class InternRoleTrackOut(BaseModel):
    id: int
    title: str
    domain: str
    required_skills_json: str
    description: Optional[str] = None
    duration_months: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
