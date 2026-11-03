import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.content import Service, Enquiry
from app.models.user import User

client = TestClient(app)

def test_public_pages_render():
    """Verify that all public pages return 200 OK and render correctly"""
    routes = ["/", "/about", "/services", "/industries", "/products", "/portfolio", "/training", "/contact", "/login"]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Failed on route {route}"
        assert "CAC" in response.text or "CTRL ALT CRAC" in response.text

def test_services_api():
    """Verify listing services via public API"""
    response = client.get("/api/v1/services/")
    assert response.status_code == 200
    services = response.json()
    assert len(services) >= 6
    assert any("Machine Learning" in s["title"] for s in services)

def test_industries_api():
    """Verify listing target industries via public API"""
    response = client.get("/api/v1/industries/")
    assert response.status_code == 200
    industries = response.json()
    assert len(industries) >= 6
    assert any("Healthcare" in ind["name"] for ind in industries)

def test_enquiry_submission_and_lead_scoring():
    """Verify inbound lead submission and automatic qualification scoring"""
    payload = {
        "name": "David Miller",
        "email": "d.miller@globalfintech.com",
        "company": "Global FinTech Partners",
        "industry": "Finance",
        "service_interest": "RAG & Enterprise Document Intelligence",
        "budget": "$30k - $75k",
        "timeline": "Immediate (1-2 weeks)",
        "message": "We need to ingest 20,000 internal loan disclosures into a secure, tenant-isolated vector store with page citations."
    }
    response = client.post("/api/v1/enquiries/public", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "d.miller@globalfintech.com"
    # Should be auto-qualified due to high budget and immediate timeline
    assert data["lead_score"] >= 70
    assert data["status"] == "qualified"

def test_ai_agent_chat():
    """Verify AI Agent chat response and tool execution"""
    payload = {
        "message": "What is the estimated budget and timeline for an enterprise AI assistant?",
        "agent_code": "website_support"
    }
    response = client.post("/api/v1/agents/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["agent_code"] == "website_support"
    assert data["latency_ms"] > 0

def test_rag_query_engine():
    """Verify RAG retrieval over company knowledge base"""
    payload = {
        "query": "What are the core value proposition and delivery pillars of CAC?",
        "top_k": 2
    }
    response = client.post("/api/v1/knowledge-bases/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    assert "doc_title" in data["sources"][0]

def test_auth_login():
    """Verify user login and JWT issuance"""
    payload = {
        "email": "admin@cac-innovations.com",
        "password": "Admin@123456"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@cac-innovations.com"
