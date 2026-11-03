from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_admin
from app.models.content import Enquiry
from app.models.user import User
from app.schemas.content import EnquiryCreate, EnquiryUpdateStatus, EnquiryOut
from app.services.crm_service import CRMService

router = APIRouter(prefix="/enquiries", tags=["Lead Generation & Enquiries"])

@router.post("/public", response_model=EnquiryOut, status_code=status.HTTP_201_CREATED)
def submit_enquiry_public(enquiry_in: EnquiryCreate, db: Session = Depends(get_db)):
    """Public lead submission from website and consultation forms"""
    created = CRMService.create_enquiry(db, enquiry_in)
    return created

@router.get("/admin", response_model=List[EnquiryOut])
def list_enquiries_admin(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin endpoint to view, filter and qualify pipeline enquiries"""
    query = db.query(Enquiry)
    if status_filter:
        query = query.filter(Enquiry.status == status_filter)
    return query.order_by(Enquiry.lead_score.desc(), Enquiry.created_at.desc()).all()

@router.patch("/{enquiry_id}/status", response_model=EnquiryOut)
def update_enquiry_status(
    enquiry_id: int,
    update_data: EnquiryUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    updated = CRMService.update_status(db, enquiry_id, update_data, current_user.email)
    if not updated:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return updated
