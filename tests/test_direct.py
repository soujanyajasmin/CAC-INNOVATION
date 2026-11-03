import pytest
from app.database.session import SessionLocal
from app.database.init_db import init_database
from app.models.content import Service, Industry, PortfolioProject, Enquiry
from app.models.user import User, Role
from app.models.client_project import Client, Project, Task, Invoice, Notification
from app.schemas.content import EnquiryCreate
from app.schemas.client_project import ConvertLeadRequest, TaskCreate, TaskSubmit, TaskReview
from app.services.crm_service import CRMService
from app.services.project_service import ProjectWorkflowService
from app.services.ai_service.rag_engine import RAGEngine
from app.services.ai_service.agent_manager import AgentManager
from app.routers import services, industries, portfolio

@pytest.fixture(scope="function")
def db():
    init_database(seed_demo=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_six_roles_and_users(db):
    """Verify that all 6 roles and associated test users exist"""
    roles = [r.name for r in db.query(Role).all()]
    expected_roles = ["super_admin", "admin", "manager", "employee", "intern", "client"]
    for er in expected_roles:
        assert er in roles, f"Role {er} is missing"

    manager = db.query(User).filter(User.email == "manager@cac-innovations.com").first()
    assert manager is not None
    assert manager.role.name == "manager"

    dev = db.query(User).filter(User.email == "dev@cac-innovations.com").first()
    assert dev is not None
    assert dev.role.name == "employee"

    intern = db.query(User).filter(User.email == "intern@cac-innovations.com").first()
    assert intern is not None
    assert intern.role.name == "intern"

def test_lead_generation_and_scoring(db):
    """Verify inbound lead creation and automatic AI qualification scoring"""
    req = EnquiryCreate(
        name="Elena Rostova",
        email="elena@biotech-systems.com",
        company="BioTech Systems",
        industry="Healthcare",
        service_interest="RAG & Enterprise Document Intelligence",
        budget="$30k - $75k",
        timeline="Immediate (1-2 weeks)",
        message="We need a tenant-isolated RAG pipeline to search proprietary clinical research protocols."
    )
    enquiry = CRMService.create_enquiry(db, req)
    assert enquiry.id is not None
    assert enquiry.lead_score >= 70
    assert enquiry.status in ["qualified", "new_enquiry"]

def test_lead_conversion_to_client_and_project(db):
    """Verify 1-click conversion from won lead to client & project with manager assignment"""
    lead = db.query(Enquiry).filter(Enquiry.company == "BioTech Systems").first()
    manager = db.query(User).filter(User.email == "manager@cac-innovations.com").first()
    admin = db.query(User).filter(User.email == "admin@cac-innovations.com").first()

    req = ConvertLeadRequest(
        lead_id=lead.id,
        project_title="BioTech Clinical Search Engine",
        manager_id=manager.id,
        budget="$45,000"
    )
    project = ProjectWorkflowService.convert_lead_to_client_and_project(db, req, admin)
    assert project.id is not None
    assert project.manager_id == manager.id
    assert project.client.name == "BioTech Systems"
    assert lead.status == "won"

def test_task_lifecycle_workflow(db):
    """Verify task assignment -> submit with PR link -> manager approval flow"""
    manager = db.query(User).filter(User.email == "manager@cac-innovations.com").first()
    intern = db.query(User).filter(User.email == "intern@cac-innovations.com").first()
    project = db.query(Project).first()

    # 1. Manager assigns task to Intern
    task_in = TaskCreate(
        project_id=project.id,
        title="Implement sliding window document chunker",
        description="Write text chunking with 50-word overlap",
        assigned_to_id=intern.id,
        priority="High"
    )
    task = ProjectWorkflowService.assign_task(db, task_in, manager)
    assert task.status == "Assigned"

    # 2. Intern submits work with GitHub PR link
    sub = TaskSubmit(
        pr_url="https://github.com/cac-innovations/project/pull/42",
        branch_name="feature/chunker",
        submission_notes="Implemented sliding window with tests passing."
    )
    task = ProjectWorkflowService.submit_task_work(db, task.id, sub, intern)
    assert task.status == "Under Review"

    # 3. Manager approves work
    rev = TaskReview(status="Approved", review_feedback="Verified and merged.")
    task = ProjectWorkflowService.review_task(db, task.id, rev, manager)
    assert task.status == "Approved"
    assert task.approved_by_id == manager.id

def test_role_scoped_ai_assistants(db):
    """Verify role-aware AI capabilities for Manager, Intern, and Client"""
    # Manager
    mgr_res = AgentManager.chat_with_agent(
        db=db,
        session_id="s_mgr",
        message="Give me a progress summary and plan",
        user_role="manager"
    )
    assert "Manager Executive Briefing" in mgr_res["reply"] or "plan" in mgr_res["reply"].lower()

    # Intern
    intern_res = AgentManager.chat_with_agent(
        db=db,
        session_id="s_int",
        message="How should I submit my code?",
        user_role="intern"
    )
    assert "Intern Mentor" in intern_res["reply"] or "Pull Request" in intern_res["reply"]

def test_rag_query_engine(db):
    """Verify RAG retrieval and citation generation"""
    result = RAGEngine.query_with_rag(
        db=db,
        query="What is the architecture blueprint and delivery model of CAC Innovation?",
        top_k=2
    )
    assert "answer" in result
    assert "sources" in result
    assert result["latency_ms"] > 0

def test_admin_employee_provisioning(db):
    """Verify that admin can provision new employee credentials and revoke them"""
    from app.routers.auth import create_employee_credentials, delete_employee_account
    from app.schemas.user import UserCreate
    from unittest.mock import MagicMock
    
    admin = db.query(User).filter(User.email == "admin@cac-innovations.com").first()
    req_mock = MagicMock()
    req_mock.client.host = "127.0.0.1"

    # 1. Admin provisions a new Developer
    new_emp_data = UserCreate(
        full_name="Sarah Connor",
        email="s.connor@cac-innovations.com",
        password="CyberPass@2026",
        role_name="employee",
        title="Senior Security AI Engineer",
        department="Defensive AI"
    )
    created_emp = create_employee_credentials(new_emp_data, req_mock, db, admin)
    assert created_emp.id is not None
    assert created_emp.email == "s.connor@cac-innovations.com"
    assert created_emp.role.name == "employee"

    # 2. Verify password hashing works
    from app.core.security import verify_password
    assert verify_password("CyberPass@2026", created_emp.hashed_password)

    # 3. Admin revokes account
    del_res = delete_employee_account(created_emp.id, req_mock, db, admin)
    assert "deleted successfully" in del_res["message"]
    assert db.query(User).filter(User.id == created_emp.id).first() is None

def test_ceo_portal_and_security_alerts(db):
    """Verify CEO login rules on standard portal vs /ceo portal, and role selection validation"""
    from fastapi import HTTPException
    from app.routers.auth import login_json, ceo_standard_login_attempts
    from app.schemas.user import LoginRequest
    from unittest.mock import MagicMock

    ceo_standard_login_attempts.clear()
    req_mock = MagicMock()
    req_mock.client.host = "192.168.1.100"
    res_mock = MagicMock()

    # 1. 1st attempt using CEO credentials on standard portal (/login)
    ceo_req_1 = LoginRequest(
        email="ceo@cac-innovations.com",
        password="Ceo@123456",
        login_type="admin",
        is_ceo_portal=False
    )
    with pytest.raises(HTTPException) as exc_info1:
        login_json(ceo_req_1, res_mock, req_mock, db)
    assert exc_info1.value.status_code == 403
    assert "WARNING:" in exc_info1.value.detail
    assert "Attempt 1 of 2" in exc_info1.value.detail

    # 2. 2nd attempt using CEO credentials on standard portal (/login) -> ALERTS & BLOCKS
    with pytest.raises(HTTPException) as exc_info2:
        login_json(ceo_req_1, res_mock, req_mock, db)
    assert exc_info2.value.status_code == 403
    assert "SECURITY ALERT:" in exc_info2.value.detail
    assert "twice" in exc_info2.value.detail

    # 3. CEO credentials on dedicated CEO Portal (/ceo) -> SUCCESS
    ceo_portal_req = LoginRequest(
        email="ceo@cac-innovations.com",
        password="Ceo@123456",
        is_ceo_portal=True
    )
    token_res = login_json(ceo_portal_req, res_mock, req_mock, db)
    assert token_res.access_token is not None
    assert token_res.user.email == "ceo@cac-innovations.com"

    # 4. Role Type Selection verification:
    # A regular user (intern) trying to select 'manager' -> Role Mismatch
    intern_req_mismatch = LoginRequest(
        email="intern@cac-innovations.com",
        password="Intern@123456",
        login_type="manager",
        is_ceo_portal=False
    )
    with pytest.raises(HTTPException) as exc_mismatch:
        login_json(intern_req_mismatch, res_mock, req_mock, db)
    assert exc_mismatch.value.status_code == 400
    assert "Role Type Mismatch" in exc_mismatch.value.detail

    # Matching role -> SUCCESS
    intern_req_match = LoginRequest(
        email="intern@cac-innovations.com",
        password="Intern@123456",
        login_type="intern",
        is_ceo_portal=False
    )
    intern_token = login_json(intern_req_match, res_mock, req_mock, db)
    assert intern_token.access_token is not None

def test_admin_technology_intern_roles_and_direct_project(db):
    """Verify that Admin can create new technology, new intern role track, developer of specific technology, and direct project"""
    from app.routers.technologies import create_technology, create_intern_role
    from app.routers.projects import create_project_direct
    from app.routers.auth import create_employee_credentials
    from app.schemas.technology import TechnologyCreate, InternRoleTrackCreate
    from app.schemas.client_project import DirectProjectCreate
    from app.schemas.user import UserCreate
    from unittest.mock import MagicMock

    admin = db.query(User).filter(User.email == "admin@cac-innovations.com").first()
    req_mock = MagicMock()
    req_mock.client.host = "127.0.0.1"

    from app.models.technology import Technology, InternRoleTrack
    # Clean up prior test runs
    db.query(Technology).filter(Technology.name == "Golang").delete()
    db.query(InternRoleTrack).filter(InternRoleTrack.title == "Blockchain & Web3 Intern").delete()
    db.query(User).filter(User.email == "raj.mobile@cac-innovations.com").delete()
    existing_proj = db.query(Project).filter(Project.title == "OmniTrack Global Logistics Platform").first()
    if existing_proj:
        db.delete(existing_proj)
    db.commit()

    # 1. Admin adds a new technology
    new_tech = create_technology(
        TechnologyCreate(name="Golang", category="Backend", description="High-throughput cloud microservices"),
        req_mock, db, admin
    )
    assert new_tech.id is not None
    assert new_tech.name == "Golang"

    # 2. Admin adds a new type role of intern
    new_intern_role = create_intern_role(
        InternRoleTrackCreate(
            title="Blockchain & Web3 Intern",
            domain="Decentralized Tech",
            required_skills=["Golang", "Docker", "Cryptography"],
            description="Smart contract development and node infrastructure",
            duration_months=4
        ),
        req_mock, db, admin
    )
    assert new_intern_role.id is not None
    assert new_intern_role.title == "Blockchain & Web3 Intern"

    # 3. Admin provisions a new developer of different technology (e.g. Flutter Mobile Developer)
    mobile_dev = create_employee_credentials(
        UserCreate(
            full_name="Raj Patel",
            email="raj.mobile@cac-innovations.com",
            password="MobileDevPass#2026",
            role_name="employee",
            title="Senior Flutter Mobile Engineer",
            department="Mobile App Division",
            skills=["Flutter", "Dart", "FastAPI"]
        ),
        req_mock, db, admin
    )
    assert mobile_dev.id is not None
    assert "Flutter" in mobile_dev.skills_json

    # 4. Admin creates a new project directly
    direct_proj = create_project_direct(
        DirectProjectCreate(
            title="OmniTrack Global Logistics Platform",
            client_name="Titan Supply Chain Corp",
            tech_stack=["Golang", "Flutter", "PostgreSQL"],
            budget="$48,000",
            description="Cross-platform vehicle tracking and telemetry APIs"
        ),
        db, admin
    )
    assert direct_proj.id is not None
    assert direct_proj.client.name == "Titan Supply Chain Corp"
    assert "Golang" in direct_proj.tech_stack_json

def test_admin_assigns_client_to_manager_and_manager_assigns_tasks(db):
    """Verify workflow:
    1. Admin assigns client to manager
    2. Manager assigns task to developer and intern
    3. Developer and intern submit work
    4. Manager reviews and approves both
    """
    from app.routers.projects import assign_client_manager_endpoint, assign_new_task, submit_task, review_task
    from app.schemas.client_project import AssignClientManagerRequest, TaskCreate, TaskSubmit, TaskReview
    
    admin = db.query(User).filter(User.email == "admin@cac-innovations.com").first()
    manager = db.query(User).filter(User.email == "manager@cac-innovations.com").first()
    dev = db.query(User).filter(User.email == "dev@cac-innovations.com").first()
    intern = db.query(User).filter(User.email == "intern@cac-innovations.com").first()
    
    # Create test client and project
    client = db.query(Client).filter(Client.code == "TEST-ACME").first()
    if not client:
        client = Client(name="Acme Corp Test", code="TEST-ACME", industry="Robotics")
        db.add(client)
        db.commit()
        db.refresh(client)
        
    project = db.query(Project).filter(Project.title == "Acme Core Automation").first()
    if not project:
        project = Project(client_id=client.id, title="Acme Core Automation", status="in_progress")
        db.add(project)
        db.commit()
        db.refresh(project)

    # 1. Admin assigns the Client to the Manager
    res_client = assign_client_manager_endpoint(client.id, AssignClientManagerRequest(manager_id=manager.id), db, admin)
    assert res_client.manager_id == manager.id
    
    db.refresh(client)
    assert client.manager_id == manager.id

    # 2. Manager assigns task to Developer
    dev_task = assign_new_task(
        TaskCreate(
            project_id=project.id,
            title="Build Kafka telemetry stream ingestor",
            description="High throughput consumer with avro serialization",
            assigned_to_id=dev.id,
            priority="High"
        ),
        db, manager
    )
    assert dev_task.id is not None
    assert dev_task.assigned_to_id == dev.id
    assert dev_task.status == "Assigned"

    # 3. Manager assigns task to Intern
    intern_task = assign_new_task(
        TaskCreate(
            project_id=project.id,
            title="Write unit tests for telemetry validation",
            description="Pytest test suite testing invalid packet handling and null safety",
            assigned_to_id=intern.id,
            priority="Medium"
        ),
        db, manager
    )
    assert intern_task.id is not None
    assert intern_task.assigned_to_id == intern.id
    assert intern_task.status == "Assigned"

    # 4. Developer submits work
    dev_sub = submit_task(
        dev_task.id,
        TaskSubmit(
            pr_url="https://github.com/cac-innovations/project/pull/42",
            branch_name="feature/kafka-ingest",
            submission_notes="Telemetry consumer ready with end-to-end integration tests."
        ),
        db, dev
    )
    assert dev_sub.status == "Under Review"

    # 5. Intern submits work
    intern_sub = submit_task(
        intern_task.id,
        TaskSubmit(
            pr_url="https://github.com/cac-innovations/project/pull/43",
            branch_name="feature/telemetry-tests",
            submission_notes="Pytest suite with 100% coverage across telemetry packets."
        ),
        db, intern
    )
    assert intern_sub.status == "Under Review"

    # 6. Manager reviews and approves both
    dev_reviewed = review_task(
        dev_task.id,
        TaskReview(status="Approved", review_feedback="Outstanding work, merged to main."),
        db, manager
    )
    assert dev_reviewed.status == "Approved"
    assert dev_reviewed.approved_by_id == manager.id

    intern_reviewed = review_task(
        intern_task.id,
        TaskReview(status="Approved", review_feedback="Excellent unit tests, high coverage."),
        db, manager
    )
    assert intern_reviewed.status == "Approved"
    assert intern_reviewed.approved_by_id == manager.id

