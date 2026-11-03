from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import get_current_user, get_current_user_optional, require_admin
from app.models.ai import KnowledgeBase, KBDocument
from app.models.user import User
from app.schemas.ai import (
    KnowledgeBaseCreate, KnowledgeBaseOut, KBDocumentOut,
    RAGQueryRequest, RAGQueryResponse
)
from app.services.ai_service.rag_engine import RAGEngine

router = APIRouter(prefix="/knowledge-bases", tags=["RAG & Document Intelligence"])

@router.get("/", response_model=List[KnowledgeBaseOut])
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    query = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
    if current_user and current_user.role.name == "client":
        query = query.filter((KnowledgeBase.tenant_id == current_user.tenant_id) | (KnowledgeBase.tenant_id == None))
    elif not current_user or current_user.role.name not in ["super_admin", "admin"]:
        query = query.filter(KnowledgeBase.tenant_id == None)
    return query.all()

@router.post("/", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    kb = KnowledgeBase(**kb_in.model_dump())
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb

@router.post("/{kb_id}/documents", response_model=KBDocumentOut)
def upload_and_ingest_document(
    kb_id: int,
    title: str,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    doc = RAGEngine.ingest_document(db, kb_id, title, content)
    return doc

@router.post("/query", response_model=RAGQueryResponse)
def query_knowledge_base(
    req: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    tenant_id = current_user.tenant_id if current_user and current_user.tenant_id else None
    result = RAGEngine.query_with_rag(
        db=db,
        query=req.query,
        kb_id=req.kb_id,
        tenant_id=tenant_id,
        top_k=req.top_k or 3
    )
    return RAGQueryResponse(**result)
