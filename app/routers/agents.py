import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import get_current_user_optional, require_admin
from app.models.ai import AIAgent, AIUsageLog
from app.models.user import User
from app.schemas.ai import AIAgentCreate, AIAgentOut, AgentChatRequest, AgentChatResponse
from app.services.ai_service.agent_manager import AgentManager

router = APIRouter(prefix="/agents", tags=["AI Agents & Orchestration"])

@router.get("/", response_model=List[AIAgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.query(AIAgent).filter(AIAgent.is_active == True).all()

@router.post("/", response_model=AIAgentOut, status_code=status.HTTP_201_CREATED)
def register_agent(
    agent_in: AIAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    agent = AIAgent(**agent_in.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    chat_req: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    session_id = chat_req.session_id or str(uuid.uuid4())
    tenant_id = current_user.tenant_id if current_user and current_user.tenant_id else None
    user_role = current_user.role.name if current_user and current_user.role else "public"
    
    result = AgentManager.chat_with_agent(
        db=db,
        session_id=session_id,
        message=chat_req.message,
        agent_code=chat_req.agent_code or "website_support",
        tenant_id=tenant_id,
        user_role=user_role
    )
    return AgentChatResponse(**result)

@router.get("/metrics/usage")
def get_usage_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    total_calls = db.query(AIUsageLog).count()
    logs = db.query(AIUsageLog).order_by(AIUsageLog.created_at.desc()).limit(15).all()
    avg_latency = 0
    if logs:
        avg_latency = round(sum(l.latency_ms for l in logs) / len(logs), 2)
    return {
        "total_calls": total_calls,
        "recent_logs": logs,
        "avg_latency_ms": avg_latency
    }
