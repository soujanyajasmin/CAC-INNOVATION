from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleOut(RoleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    title: Optional[str] = None
    department: Optional[str] = None
    skills_json: Optional[str] = "[]"
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    role_name: str = "employee"
    skills: Optional[List[str]] = None
    tenant_id: Optional[int] = None

class UserOut(UserBase):
    id: int
    role: Optional[RoleOut] = None
    tenant_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: str
    password: str
    login_type: Optional[str] = None
    is_ceo_portal: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
