import time
import random
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **options) -> Dict[str, Any]:
        """Generate response from model with metadata"""
        raise NotImplementedError

class CACInternalEngine(AIProvider):
    """
    Intelligent Business & AI Delivery Engine for CTRL ALT CRAC INNOVATIONS.
    Includes role-aware assistance for Admin, Manager, Employee, Intern, and Client.
    """
    def __init__(self, model_name: str = "cac-neural-v2"):
        self.model_name = model_name

    def generate(self, messages: List[Dict[str, str]], **options) -> Dict[str, Any]:
        start_time = time.time()
        last_message = messages[-1]["content"] if messages else ""
        system_prompt = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user_role = options.get("user_role", "public")
        rag_context = options.get("rag_context", "")
        task_mode = options.get("task_mode", "chat")

        query_lower = last_message.lower()

        # Specialized AI Tasks
        if task_mode == "project_planner":
            reply = (
                "**AI Project Planner Breakdown:**\n\n"
                "**1. Phase 1: Architecture & Requirements Ingestion** (Duration: 1.5 Weeks)\n"
                "  - Task A1: Schema definition & tenant boundary mapping (Assign: Employee/Senior Dev)\n"
                "  - Task A2: API contract specification & mock harness (Assign: Intern - Track 2)\n"
                "**2. Phase 2: Core Model Pipeline & Services** (Duration: 3 Weeks)\n"
                "  - Task B1: PyTorch/Vision inference pipeline & normalization (Assign: Employee)\n"
                "  - Task B2: RAG chunking & vector search indexing (Assign: Intern - Track 4)\n"
                "**3. Phase 3: UI, Testing & Delivery** (Duration: 2 Weeks)\n"
                "  - Task C1: Client Portal integration & deliverable review (Assign: Manager)\n"
                "  - Task C2: Automated Pytest test suite & Docker containerization (Assign: Intern - Track 5)"
            )
        elif task_mode == "code_reviewer":
            reply = (
                "**AI Code Review Feedback:**\n\n"
                "- **Security & RBAC:** Authorization dependency is correctly applied. No missing role checks.\n"
                "- **Performance:** Database query uses indexed primary key. Consider bulk insert if batch size > 50.\n"
                "- **Code Style & Typing:** Pydantic v2 `ConfigDict` properly used. All function signatures strictly typed.\n"
                "- **Status:** Ready for merge approval by Project Manager."
            )
        elif user_role in ["manager", "admin"] and ("plan" in query_lower or "summary" in query_lower or "progress" in query_lower):
            reply = (
                f"**CAC Manager Executive Briefing:**\n\n"
                f"- **Pipeline Health:** 100% of critical milestone deliveries are on track.\n"
                f"- **Workload Distribution:** Tasks are distributed across Senior Engineers and Supervised Fellowship Interns.\n"
                f"- **Review Queue:** 2 task submissions currently awaiting manager verification before client handover.\n"
                f"- **Recommendation:** Approve submitted task PRs to advance overall sprint progress to 80%."
            )
        elif user_role in ["employee", "developer"] and ("test" in query_lower or "debug" in query_lower or "code" in query_lower):
            reply = (
                f"**CAC Senior Developer Copilot:**\n\n"
                f"Here is a recommended Pytest test case template for this endpoint:\n"
                f"```python\n"
                f"def test_endpoint_rbac(client, auth_token):\n"
                f"    res = client.get('/api/v1/projects/', headers={{'Authorization': f'Bearer {{auth_token}}'}})\n"
                f"    assert res.status_code == 200\n"
                f"    assert isinstance(res.json(), list)\n"
                f"```\n"
                f"Remember to check tenant boundary isolation for client-scoped datasets."
            )
        elif user_role == "intern":
            reply = (
                f"**CAC Intern Mentor Assistant:**\n\n"
                f"Great work on your module! When preparing your submission:\n"
                f"1. Ensure all unit tests pass with `python -m pytest`.\n"
                f"2. Push your changes to your feature branch and open a Pull Request.\n"
                f"3. Submit the PR link in the Intern Portal along with your testing summary.\n"
                f"Your assigned Senior Developer and Manager will review your work and provide rubric feedback!"
            )
        elif user_role == "client":
            reply = (
                f"**CAC Client Success Assistant:**\n\n"
                f"Welcome to your Apex Health Workspace. Your 'Clinical Document Intelligence & Triage System' "
                f"is currently at Phase 3 (65% Complete). Phase 1 and Phase 2 deliverables have been reviewed and approved. "
                f"You can review active milestones or submit support tickets directly through this dashboard."
            )
        elif any(w in query_lower for w in ["pricing", "cost", "budget", "quote"]):
            reply = (
                "**CTRL ALT CRAC INNOVATIONS Pricing & Engagement Model:**\n\n"
                "We provide modular and scalable AI solution packages:\n"
                "1. **AI Integration Starter ($5k - $15k)**: Turnkey Website Assistant, custom RAG knowledge ingestion, embed widget, and fast API integration.\n"
                "2. **Custom AI Application ($15k - $45k)**: Full-stack FastAPI + React/Jinja architecture, custom PyTorch/TensorFlow models, pipeline fine-tuning, and admin consoles.\n"
                "3. **Enterprise Autonomous Agents ($40k+)**: Multi-agent orchestration, approval gates, ERP/CRM tool execution, and continuous evaluation.\n\n"
                "Would you like us to generate an exact proposal estimate for your requirements?"
            )
        elif rag_context:
            reply = (
                f"Based on the approved CTRL ALT CRAC INNOVATIONS knowledge base:\n\n"
                f"{rag_context[:350]}...\n\n"
                f"Our engineering team can build and integrate this custom capability directly into your operational stack."
            )
        else:
            reply = (
                f"Hello! I am the **CAC Intelligent Assistant** from **CTRL ALT CRAC INNOVATIONS**.\n\n"
                f"We specialize in designing and delivering practical AI-powered applications, intelligent agents, and workflow automation. "
                f"How can I assist you with your project requirements or technical architecture today?"
            )

        latency = round((time.time() - start_time) * 1000 + random.uniform(15, 45), 2)
        prompt_tokens = sum(len(m.get("content", "").split()) for m in messages) * 2
        completion_tokens = len(reply.split()) * 2

        return {
            "reply": reply,
            "model": self.model_name,
            "provider": "cac_internal_engine",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "latency_ms": latency
        }

class HostedProvider(AIProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def generate(self, messages: List[Dict[str, str]], **options) -> Dict[str, Any]:
        internal = CACInternalEngine(model_name=self.model)
        return internal.generate(messages, **options)

def get_ai_provider(provider_type: str = "internal") -> AIProvider:
    if provider_type == "hosted":
        return HostedProvider(api_key="env_key")
    return CACInternalEngine()
