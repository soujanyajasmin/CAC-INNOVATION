import json
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.permissions import get_current_user, require_admin, require_super_admin
from app.models.user import User, Role
from app.models.audit import AuditLog
from app.schemas.user import LoginRequest, TokenResponse, UserOut, UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory tracking of CEO login attempts on standard employee login portal
# Key: client_ip (or email), Value: int count
ceo_standard_login_attempts: dict = {}

def is_ceo_account(user: User) -> bool:
    """Helper to detect if a user account is the Chief Executive Officer"""
    if not user:
        return False
    email_clean = user.email.strip().lower()
    if email_clean in ["ceo@cac-innovations.com", "admin@cac-innovations.com"]:
        return True
    if user.title and ("ceo" in user.title.lower() or "chief executive" in user.title.lower()):
        return True
    return False

@router.post("/token", response_model=dict)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username.strip().lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.name if user.role else "client"}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login_json(
    credentials: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    email_clean = credentials.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    client_ip = request.client.host if request.client else "standard"
    user_is_ceo = is_ceo_account(user)

    # 1. SPECIAL CEO SECURITY POLICY
    # If logging in from the standard portal (/login) with CEO credentials:
    if user_is_ceo and not credentials.is_ceo_portal:
        current_attempts = ceo_standard_login_attempts.get(client_ip, 0) + 1
        ceo_standard_login_attempts[client_ip] = current_attempts

        if current_attempts == 1:
            # 1st attempt: Warning
            audit = AuditLog(
                user_id=user.id,
                user_email=user.email,
                action="CEO_LOGIN_WARNING",
                ip_address=client_ip,
                details="CEO credentials detected on standard login portal (/login). Warning issued: Executive leadership must log in via /ceo."
            )
            db.add(audit)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="WARNING: Executive CEO credentials detected on the standard employee login portal. For security and governance protocols, Executive Leadership must log in via the dedicated Executive CEO Portal at /ceo. (Attempt 1 of 2 recorded - Warning issued)."
            )
        else:
            # 2nd attempt or more: Security Alert
            audit = AuditLog(
                user_id=user.id,
                user_email=user.email,
                action="CEO_SECURITY_ALERT_LOCKED",
                ip_address=client_ip,
                details="SECURITY ALERT: Second attempt using CEO credentials on standard portal (/login). Standard portal access locked. Redirecting to /ceo."
            )
            db.add(audit)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SECURITY ALERT: Executive CEO credentials have been entered on the standard employee portal twice! An executive security alert has been dispatched and logged in the Security Audit Trail. Standard portal access is locked for this role. You MUST use the dedicated Executive Portal at /ceo."
            )

    # 2. RESTRICT CEO PORTAL (/ceo) TO EXECUTIVES ONLY
    if credentials.is_ceo_portal and not user_is_ceo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: The Executive CEO Portal is restricted to Chief Executive Officers only. Staff members must log in via the standard portal at /login."
        )

    # If CEO logged in successfully via /ceo, clear attempt counter
    if user_is_ceo and credentials.is_ceo_portal:
        ceo_standard_login_attempts.pop(client_ip, None)

    # 3. ROLE TYPE VALIDATION (When logging in through standard portal)
    if credentials.login_type and not credentials.is_ceo_portal:
        user_role_name = user.role.name if user.role else "client"
        allowed = False
        if credentials.login_type == "admin" and user_role_name in ["admin", "super_admin"]:
            allowed = True
        elif credentials.login_type == user_role_name:
            allowed = True

        if not allowed:
            role_display = {
                "super_admin": "Super Admin / Director",
                "admin": "Admin / Business Development",
                "manager": "Project Manager",
                "employee": "Developer",
                "intern": "Intern",
                "client": "Client Stakeholder"
            }.get(user_role_name, user_role_name)

            selected_display = {
                "admin": "Admin / Business Development",
                "manager": "Project Manager",
                "employee": "Developer",
                "intern": "Intern",
                "client": "Client Stakeholder"
            }.get(credentials.login_type, credentials.login_type)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role Type Mismatch: Your account is registered as '{role_display}', but you selected '{selected_display}'. Please select the matching role type."
            )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.name if user.role else "client"}
    )
    
    # Set HTTP-only session cookie for smooth browser experience
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False # set to True when using HTTPS in production
    )

    # Audit log
    audit_action = "CEO_EXECUTIVE_LOGIN" if (user_is_ceo and credentials.is_ceo_portal) else "USER_LOGIN"
    audit = AuditLog(
        user_id=user.id,
        user_email=user.email,
        action=audit_action,
        ip_address=client_ip,
        details=f"User {user.email} authenticated successfully as {user.role.name if user.role else 'user'} via {'CEO Portal (/ceo)' if credentials.is_ceo_portal else 'Standard Portal (/login)'}"
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: List all registered employees, managers, interns, and clients"""
    return db.query(User).order_by(User.id.desc()).all()

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_employee_credentials(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Create employee credentials (Manager, Dev, Intern, BD, Client)"""
    email = user_in.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{email}' already exists."
        )

    role = db.query(Role).filter(Role.name == user_in.role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_in.role_name}' does not exist. Available: super_admin, admin, manager, employee, intern, client."
        )

    # Only super_admin can create other super_admins
    if user_in.role_name == "super_admin" and current_user.role.name != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Super Admin can create another Super Admin account."
        )

    skills_json_str = "[]"
    if user_in.skills:
        skills_json_str = json.dumps(user_in.skills)
    elif user_in.skills_json:
        skills_json_str = user_in.skills_json

    new_user = User(
        email=email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        title=user_in.title,
        department=user_in.department,
        skills_json=skills_json_str,
        role_id=role.id,
        tenant_id=user_in.tenant_id,
        is_active=user_in.is_active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="USER_CREATED",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {current_user.email} created credentials for {new_user.email} with role '{role.name}'"
    )
    db.add(audit)
    db.commit()

    return new_user

@router.delete("/users/{user_id}")
def delete_employee_account(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Remove or deactivate an employee account"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own active administrator account."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email == "admin@cac-innovations.com":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete root system Super Admin.")

    target_email = user.email
    db.delete(user)
    db.commit()

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="USER_DELETED",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {current_user.email} removed user account {target_email}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"User account {target_email} deleted successfully."}
