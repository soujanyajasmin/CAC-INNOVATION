import json
import uuid
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.ai import AIAgent, AIUsageLog, ConversationMessage
from app.models.audit import AuditLog
from app.services.ai_service.provider import get_ai_provider
from app.services.ai_service.rag_engine import RAGEngine

class AgentManager:
    @staticmethod
    def execute_tool(tool_name: str, args: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Executes an approved, bounded tool within safety parameters.
        """
        if tool_name == "calculate_estimate":
            scope = args.get("scope", "starter").lower()
            complexity = args.get("complexity", "standard").lower()
            base = 8000
            if "custom" in scope or "app" in scope:
                base = 25000
            elif "enterprise" in scope or "agent" in scope:
                base = 45000
            if complexity == "high":
                base = int(base * 1.5)
            return {
                "success": True,
                "estimated_range": f"${base:,} - ${int(base * 1.35):,}",
                "typical_timeline": "4 - 8 weeks",
                "recommended_stack": "FastAPI + SQLite/PostgreSQL + PyTorch/Transformers"
            }
            
        elif tool_name == "knowledge_search":
            query = args.get("query", "")
            passages = RAGEngine.retrieve_passages(db, query, top_k=2)
            return {
                "success": True,
                "passages_found": len(passages),
                "snippets": [p["text"][:200] + "..." for p in passages]
            }

        elif tool_name == "generate_project_plan":
            return {
                "success": True,
                "suggested_phases": 3,
                "estimated_sprint_weeks": 6,
                "recommended_roles": ["Project Manager", "Senior Dev", "2 Interns"]
            }

        elif tool_name == "schedule_consultation":
            return {
                "success": True,
                "requires_human_approval": True,
                "action": "CONSULTATION_REQUEST_QUEUED",
                "message": "Consultation request forwarded to CAC Solution Architect for human confirmation."
            }

        return {"error": f"Tool '{tool_name}' is not recognized or not permitted."}

    @classmethod
    def chat_with_agent(
        cls,
        db: Session,
        session_id: str,
        message: str,
        agent_code: str = "website_support",
        tenant_id: Optional[int] = None,
        user_role: str = "public"
    ) -> Dict[str, Any]:
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Fetch agent configuration
        agent = db.query(AIAgent).filter(AIAgent.agent_code == agent_code, AIAgent.is_active == True).first()
        if not agent:
            agent_instructions = (
                "You are the CTRL ALT CRAC INNOVATIONS Intelligent Enterprise Assistant. "
                "Help visitors explore AI services, compute project quotes, and assist team members with tasks."
            )
            permitted_tools = ["calculate_estimate", "knowledge_search", "schedule_consultation", "generate_project_plan"]
            requires_approval = False
        else:
            agent_instructions = agent.system_instructions
            try:
                permitted_tools = json.loads(agent.permitted_tools_json)
            except Exception:
                permitted_tools = ["knowledge_search"]
            requires_approval = agent.requires_human_approval

        # Store user message
        user_msg = ConversationMessage(
            session_id=session_id,
            agent_code=agent_code,
            sender="user",
            content=message
        )
        db.add(user_msg)
        db.commit()

        # Tool execution check
        tool_executed = None
        tool_result = None
        suggested_actions = ["Request a Consultation", "View AI Services", "Explore AI Internships"]
        
        msg_lower = message.lower()
        task_mode = "chat"
        if any(w in msg_lower for w in ["quote", "estimate", "cost", "how much"]):
            if "calculate_estimate" in permitted_tools:
                tool_executed = "calculate_estimate"
                tool_result = cls.execute_tool("calculate_estimate", {"scope": message, "complexity": "standard"}, db)
                suggested_actions = ["Schedule Discovery Call", "Submit Project Brief", "See Past Work"]
        elif any(w in msg_lower for w in ["plan", "breakdown", "sprint", "milestones"]):
            if "generate_project_plan" in permitted_tools or user_role in ["manager", "admin"]:
                tool_executed = "generate_project_plan"
                task_mode = "project_planner"
                tool_result = cls.execute_tool("generate_project_plan", {"project": message}, db)
                suggested_actions = ["Assign to Team", "Export Specification"]
        elif any(w in msg_lower for w in ["review", "pr", "pull request", "code check"]):
            task_mode = "code_reviewer"
            suggested_actions = ["Approve Changes", "Request Revision"]

        # Contextual search from Knowledge Base
        rag_passages = RAGEngine.retrieve_passages(db, message, tenant_id=tenant_id, top_k=2)
        kb_context = "\n".join([p["text"] for p in rag_passages]) if rag_passages else ""

        # Query provider
        provider = get_ai_provider("internal")
        chat_history = [
            {"role": "system", "content": agent_instructions},
            {"role": "user", "content": message}
        ]
        if tool_result:
            chat_history.append({"role": "system", "content": f"Tool Result: {json.dumps(tool_result)}"})
            
        gen_result = provider.generate(
            chat_history,
            rag_context=kb_context,
            user_role=user_role,
            task_mode=task_mode
        )
        reply = gen_result["reply"]

        if tool_result and "estimated_range" in tool_result:
            reply = f"Here is an indicative project estimate based on our framework:\n- **Estimated Range:** {tool_result['estimated_range']}\n- **Timeline:** {tool_result['typical_timeline']}\n- **Recommended Architecture:** {tool_result['recommended_stack']}\n\n{reply}"

        # Store assistant reply
        assistant_msg = ConversationMessage(
            session_id=session_id,
            agent_code=agent_code,
            sender="assistant",
            content=reply
        )
        db.add(assistant_msg)

        # Log AI execution usage
        latency = round((time.time() - start_time) * 1000, 2)
        usage_log = AIUsageLog(
            request_id=request_id,
            tenant_id=tenant_id,
            agent_code=agent_code,
            prompt_tokens=gen_result.get("prompt_tokens", 50),
            completion_tokens=gen_result.get("completion_tokens", 80),
            latency_ms=latency,
            status="success"
        )
        db.add(usage_log)
        db.commit()

        return {
            "session_id": session_id,
            "agent_code": agent_code,
            "reply": reply,
            "suggested_actions": suggested_actions,
            "tool_executed": tool_executed,
            "requires_approval": requires_approval,
            "tokens_used": gen_result.get("prompt_tokens", 50) + gen_result.get("completion_tokens", 80),
            "latency_ms": latency
        }
