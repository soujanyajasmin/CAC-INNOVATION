from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AIAgentBase(BaseModel):
    agent_code: str
    name: str
    description: str
    role_mission: str
    system_instructions: str
    permitted_tools_json: Optional[str] = "[]"
    requires_human_approval: Optional[bool] = False
    is_active: Optional[bool] = True
    tenant_id: Optional[int] = None

class AIAgentCreate(AIAgentBase):
    pass

class AIAgentOut(AIAgentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    tenant_id: Optional[int] = None

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KBDocumentOut(BaseModel):
    id: int
    kb_id: int
    title: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class KnowledgeBaseOut(KnowledgeBaseBase):
    id: int
    is_active: bool
    documents: List[KBDocumentOut] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RAGQueryRequest(BaseModel):
    kb_id: Optional[int] = None
    query: str
    top_k: Optional[int] = 3

class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    latency_ms: float

class AgentChatRequest(BaseModel):
    session_id: Optional[str] = None
    agent_code: Optional[str] = "website_support"
    message: str
    client_context: Optional[Dict[str, Any]] = None

class AgentChatResponse(BaseModel):
    session_id: str
    agent_code: str
    reply: str
    suggested_actions: List[str] = []
    tool_executed: Optional[str] = None
    requires_approval: bool = False
    tokens_used: int = 0
    latency_ms: float = 0.0
