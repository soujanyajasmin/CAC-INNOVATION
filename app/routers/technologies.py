import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import get_current_user, require_admin
from app.models.technology import Technology, InternRoleTrack
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.technology import (
    TechnologyCreate, TechnologyOut,
    InternRoleTrackCreate, InternRoleTrackOut
)

router = APIRouter(prefix="/technologies", tags=["Technologies & Intern Roles"])

# =========================================================================
# 1. Technologies CRUD
# =========================================================================
@router.get("/", response_model=List[TechnologyOut])
def list_technologies(db: Session = Depends(get_db)):
    """List all active technologies available across projects and roles"""
    return db.query(Technology).filter(Technology.is_active == True).order_by(Technology.category.asc(), Technology.name.asc()).all()

@router.post("/", response_model=TechnologyOut, status_code=status.HTTP_201_CREATED)
def create_technology(
    tech_in: TechnologyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Add a new technology to the company catalog"""
    name_clean = tech_in.name.strip()
    existing = db.query(Technology).filter(Technology.name.ilike(name_clean)).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.category = tech_in.category or existing.category
            existing.description = tech_in.description or existing.description
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Technology '{name_clean}' already exists."
        )

    tech = Technology(
        name=name_clean,
        category=tech_in.category.strip() if tech_in.category else "General",
        description=tech_in.description.strip() if tech_in.description else None,
        icon=tech_in.icon or "code"
    )
    db.add(tech)
    db.commit()
    db.refresh(tech)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="TECH_CREATED",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {current_user.email} added new technology: {tech.name} ({tech.category})"
    )
    db.add(audit)
    db.commit()

    return tech

@router.delete("/{tech_id}")
def delete_technology(
    tech_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Remove or deactivate a technology"""
    tech = db.query(Technology).filter(Technology.id == tech_id).first()
    if not tech:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology not found")

    tech_name = tech.name
    db.delete(tech)
    db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="TECH_DELETED",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {current_user.email} removed technology: {tech_name}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Technology '{tech_name}' deleted successfully."}

# =========================================================================
# 2. Intern Role Tracks CRUD
# =========================================================================
@router.get("/intern-roles", response_model=List[InternRoleTrackOut])
def list_intern_roles(db: Session = Depends(get_db)):
    """List all available intern roles and specialization tracks"""
    return db.query(InternRoleTrack).filter(InternRoleTrack.is_active == True).order_by(InternRoleTrack.id.asc()).all()

@router.post("/intern-roles", response_model=InternRoleTrackOut, status_code=status.HTTP_201_CREATED)
def create_intern_role(
    track_in: InternRoleTrackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Add a new intern role / domain track"""
    title_clean = track_in.title.strip()
    existing = db.query(InternRoleTrack).filter(InternRoleTrack.title.ilike(title_clean)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Intern role track '{title_clean}' already exists."
        )

    track = InternRoleTrack(
        title=title_clean,
        domain=track_in.domain.strip(),
        required_skills_json=json.dumps(track_in.required_skills),
        description=track_in.description.strip() if track_in.description else None,
        duration_months=track_in.duration_months or 3
    )
    db.add(track)
    db.commit()
    db.refresh(track)

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="INTERN_ROLE_CREATED",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {current_user.email} created new intern role: {track.title} in domain {track.domain}"
    )
    db.add(audit)
    db.commit()

    return track

@router.delete("/intern-roles/{role_id}")
def delete_intern_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint: Delete an intern role track"""
    track = db.query(InternRoleTrack).filter(InternRoleTrack.id == role_id).first()
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intern role not found")

    title = track.title
    db.delete(track)
    db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="INTERN_ROLE_DELETED",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {current_user.email} removed intern role: {title}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Intern role '{title}' deleted successfully."}
