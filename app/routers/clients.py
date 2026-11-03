from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import require_admin, get_current_user
from app.models.client_project import Client
from app.models.user import User
from app.schemas.client_project import ClientCreate, ClientOut

router = APIRouter(prefix="/clients", tags=["Clients & Tenants"])

@router.get("/", response_model=List[ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return db.query(Client).all()

@router.post("/", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing = db.query(Client).filter(Client.code == client_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client code already exists")
    client = Client(**client_in.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce tenant boundary
    if current_user.role.name == "client" and current_user.tenant_id != client_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot access other client tenant data")
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
