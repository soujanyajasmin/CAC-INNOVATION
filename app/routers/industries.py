from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_admin
from app.models.content import Industry
from app.models.user import User
from app.schemas.content import IndustryCreate, IndustryOut

router = APIRouter(prefix="/industries", tags=["Industries"])

@router.get("/", response_model=List[IndustryOut])
def list_industries(db: Session = Depends(get_db)):
    return db.query(Industry).filter(Industry.is_active == True).order_by(Industry.display_order.asc()).all()

@router.get("/{industry_id}", response_model=IndustryOut)
def get_industry(industry_id: int, db: Session = Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")
    return industry

@router.post("/", response_model=IndustryOut, status_code=status.HTTP_201_CREATED)
def create_industry(
    ind_in: IndustryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    industry = Industry(**ind_in.model_dump())
    db.add(industry)
    db.commit()
    db.refresh(industry)
    return industry
