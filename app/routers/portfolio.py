from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_admin
from app.models.content import PortfolioProject
from app.models.user import User
from app.schemas.content import PortfolioCreate, PortfolioOut

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Case Studies"])

@router.get("/", response_model=List[PortfolioOut])
def list_portfolio(db: Session = Depends(get_db)):
    return db.query(PortfolioProject).order_by(PortfolioProject.id.desc()).all()

@router.get("/{project_id}", response_model=PortfolioOut)
def get_portfolio_item(project_id: int, db: Session = Depends(get_db)):
    item = db.query(PortfolioProject).filter(PortfolioProject.id == project_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio project not found")
    return item

@router.post("/", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio_item(
    item_in: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    item = PortfolioProject(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
