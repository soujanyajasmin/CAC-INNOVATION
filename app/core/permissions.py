from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import get_token_from_request, decode_token
from app.models.user import User

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = get_token_from_request(request)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return None
    return user

def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

class RequireRole:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        user_role = user.role.name if user.role else ""
        if user_role == "super_admin":
            return user
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(self.allowed_roles)}",
            )
        return user

require_super_admin = RequireRole(["super_admin"])
require_admin = RequireRole(["super_admin", "admin"])
require_manager = RequireRole(["super_admin", "admin", "manager"])
require_trainer = RequireRole(["super_admin", "admin", "manager", "employee"]) # Aliased for intern training
require_employee = RequireRole(["super_admin", "admin", "manager", "employee"])
require_intern = RequireRole(["super_admin", "admin", "manager", "employee", "intern"])
require_client = RequireRole(["super_admin", "admin", "client"])
