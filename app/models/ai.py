from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.base import Base

class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # e.g. "cac_internal_engine", "openai", "groq", "anthropic"
    provider_type = Column(String(50), default="internal") # internal, hosted, compatible, local
    base_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # e.g. "cac-neural-v2", "gpt-4o-mini", "llama-3.3-70b"
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=False)
    context_window = Column(Integer, default=128000)
    capabilities_json = Column(Text, default='["chat", "rag", "agents", "code"]')
    is_default = Column(Boolean, default=False)
    cost_tier = Column(String(50), default="standard")

class AIAgent(Base):
    __tablename__ = "ai_agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_code = Column(String(50), unique=True, index=True, nullable=False) # "website_support", "lead_qualifier", "doc_analyst"
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    role_mission = Column(Text, nullable=False)
    system_instructions = Column(Text, nullable=False)
    permitted_tools_json = Column(Text, default='["knowledge_search", "submit_lead", "calculate_estimate"]')
    requires_human_approval = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey("clients.id"), nullable=True) # None = global/platform agent

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    tenant_id = Column(Integer, ForeignKey("clients.id"), nullable=True) # None = public company KB
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("Client", back_populates="knowledge_bases")
    documents = relationship("KBDocument", back_populates="knowledge_base", cascade="all, delete-orphan")

class KBDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    title = Column(String(200), nullable=False)
    file_path = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=False)
    chunks_json = Column(Text, default="[]") # List of text chunk strings
    status = Column(String(30), default="indexed") # pending, indexing, indexed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), index=True, nullable=False)
    tenant_id = Column(Integer, nullable=True)
    agent_code = Column(String(50), nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    status = Column(String(20), default="success") # success, error, blocked
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    agent_code = Column(String(50), default="website_support")
    sender = Column(String(20), nullable=False) # user, assistant, system, tool
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
