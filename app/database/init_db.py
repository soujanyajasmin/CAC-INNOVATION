import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.content import Service, Industry, PortfolioProject, Enquiry
from app.models.client_project import (
    Client, Project, Milestone, Task, Notification, Invoice, SupportTicket
)
from app.models.ai import AIProvider, AIModel, AIAgent, KnowledgeBase, KBDocument
from app.models.intern import InternBatch, InternTask, InternSubmission
from app.models.technology import Technology, InternRoleTrack

def init_database(seed_demo: bool = False):
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN manager_id INTEGER REFERENCES users(id)"))
            conn.commit()
        except Exception:
            pass # already added
    db = SessionLocal()
    try:
        # 1. Seed 6 Roles
        roles_data = [
            ("super_admin", "Full platform super administrative access", '["*"]'),
            ("admin", "Business Development, leads, quotes, client onboarding, project creation", '["manage_cms", "manage_crm", "manage_ai", "create_projects", "view_reports"]'),
            ("manager", "Project planning, task allocation, deadlines, workload, reviews, delivery", '["manage_projects", "assign_tasks", "approve_tasks", "review_submissions"]'),
            ("employee", "Senior engineer, development, testing, docs, task reviews", '["view_projects", "edit_tasks", "review_code", "assign_intern_tasks"]'),
            ("intern", "Intern fellowship, assigned tasks, PR submissions, progress notes", '["view_tasks", "submit_tasks", "view_learning"]'),
            ("client", "Client organization dashboard, approved milestones, deliverables, tickets", '["view_client_portal", "create_tickets", "query_kb"]')
        ]
        roles_map = {}
        for r_name, r_desc, r_perms in roles_data:
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc, permissions=r_perms)
                db.add(role)
                db.commit()
                db.refresh(role)
            roles_map[r_name] = role

        # 2. Seed Root Super Admin & Executive CEO (always present)
        admin_user = db.query(User).filter(User.email == "admin@cac-innovations.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@cac-innovations.com",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="David Sterling",
                title="Director & Super Admin",
                department="Leadership",
                role_id=roles_map["super_admin"].id,
                tenant_id=None,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        ceo_user = db.query(User).filter(User.email == "ceo@cac-innovations.com").first()
        if not ceo_user:
            ceo_user = User(
                email="ceo@cac-innovations.com",
                hashed_password=get_password_hash("Ceo@123456"),
                full_name="David Sterling",
                title="Chief Executive Officer (CEO)",
                department="Executive Leadership",
                role_id=roles_map["super_admin"].id,
                tenant_id=None,
                is_active=True
            )
            db.add(ceo_user)
            db.commit()
            db.refresh(ceo_user)

        # 3. Seed Website Services (Platform Catalog)
        services_data = [
                {
                    "slug": "ai-machine-learning",
                    "title": "Machine Learning & Predictive Analytics",
                    "short_description": "Custom statistical and ML pipelines for high-accuracy demand forecasting, risk scoring, and customer churn analysis.",
                    "full_description": "We engineer production-grade machine learning pipelines from raw data preparation and automated feature engineering to model deployment and continuous drift monitoring.",
                    "icon": "trending-up",
                    "deliverables": json.dumps(["Data preparation pipelines", "Feature stores", "Inference REST APIs", "Model drift monitors", "Evaluation reports"]),
                    "example_outcome": "94.8% accuracy in customer churn and demand forecasting.",
                    "display_order": 1
                },
                {
                    "slug": "deep-learning-computer-vision",
                    "title": "Deep Learning & Computer Vision",
                    "short_description": "Real-time object detection, defect classification, facial analysis, and biomedical image parsing using PyTorch & OpenCV.",
                    "full_description": "Our vision engineering team builds ultra-fast edge and cloud vision pipelines. From industrial surface defect detection to automated medical radiology triaging, we integrate YOLO, Vision Transformers, and custom convolutional architectures.",
                    "icon": "eye",
                    "deliverables": json.dumps(["Model training experiments", "Edge-optimized ONNX/TensorRT runtimes", "Camera stream ingestors", "Review & annotation dashboard"]),
                    "example_outcome": "Sub-20ms defect detection on manufacturing assembly lines.",
                    "display_order": 2
                },
                {
                    "slug": "nlp-generative-ai",
                    "title": "NLP & Generative AI",
                    "short_description": "Domain-specific Large Language Models, contextual summarization, structured extraction, and multilingual intelligence.",
                    "full_description": "We fine-tune and orchestrate open-weight and proprietary LLMs to process complex enterprise contracts, medical records, financial filings, and customer feedback into structured, validated JSON data.",
                    "icon": "cpu",
                    "deliverables": json.dumps(["LLM fine-tuning pipelines", "Prompt engineering frameworks", "Structured JSON extractors", "Multilingual sentiment classifiers"]),
                    "example_outcome": "85% reduction in unstructured contract processing time.",
                    "display_order": 3
                },
                {
                    "slug": "rag-document-intelligence",
                    "title": "RAG & Enterprise Document Intelligence",
                    "short_description": "Retrieval-Augmented Generation that connects LLMs to your private documentation with zero hallucinations and exact citations.",
                    "full_description": "Our RAG platform parses PDFs, scanned documents, technical schematics, and enterprise wikis into semantic vector indexes with strict tenant isolation.",
                    "icon": "file-text",
                    "deliverables": json.dumps(["Document ingestion pipelines", "Hybrid vector & BM25 search index", "Source attribution engine", "Enterprise access control filters"]),
                    "example_outcome": "Instant citation-backed answers across 50,000+ enterprise manuals.",
                    "display_order": 4
                },
                {
                    "slug": "ai-agent-development",
                    "title": "Autonomous AI Agent Workflows",
                    "short_description": "Multi-step autonomous agents equipped with approved tools, reasoning chains, and human-in-the-loop approval checkpoints.",
                    "full_description": "We build goal-driven AI agents that can query internal databases, generate reports, send notifications, and perform multi-system workflows safely.",
                    "icon": "git-branch",
                    "deliverables": json.dumps(["Agent orchestration engines", "Sandboxed tool adapters", "Human approval gates", "Detailed execution audit logs"]),
                    "example_outcome": "Multi-day manual cross-system reporting automated into 4 minutes.",
                    "display_order": 5
                },
                {
                    "slug": "ai-chatbot-development",
                    "title": "AI Chatbots & Conversational Copilots",
                    "short_description": "Context-aware conversational copilots embedded into your website, mobile app, or internal Slack/Teams workspace.",
                    "full_description": "Deliver 24/7 intelligent customer support and employee assistance. Our bots understand context, remember visitor preferences, and capture high-intent business leads.",
                    "icon": "message-square",
                    "deliverables": json.dumps(["Embeddable web widget", "Live conversation dashboard", "Human agent handoff module", "Conversation analytics"]),
                    "example_outcome": "73% automated resolution rate on tier-1 support queries.",
                    "display_order": 6
                },
                {
                    "slug": "ai-integration-automation",
                    "title": "AI Integration & Workflow Automation",
                    "short_description": "Seamless integration of AI microservices into your legacy software, ERP, CRM, and cloud infrastructure.",
                    "full_description": "Bridge the gap between modern artificial intelligence and your legacy infrastructure with secure REST/GraphQL connectors and event-driven queues.",
                    "icon": "sliders",
                    "deliverables": json.dumps(["FastAPI middleware", "Webhook event processors", "Database synchronization agents", "Developer SDK & OpenAPI specs"]),
                    "example_outcome": "Automated synchronization across Salesforce, SAP, and custom portals.",
                    "display_order": 7
                },
                {
                    "slug": "ai-powered-web-apps",
                    "title": "AI-Powered Full-Stack Applications",
                    "short_description": "End-to-end bespoke software platforms with intuitive web interfaces, real-time analytics, and embedded AI engines.",
                    "full_description": "Featuring FastAPI backends, reactive responsive user interfaces, SQLite/PostgreSQL databases, and bank-grade security protocols.",
                    "icon": "layout",
                    "deliverables": json.dumps(["Responsive UI frontend", "FastAPI production backend", "Containerized Docker configuration", "CI/CD automated testing suite"]),
                    "example_outcome": "Production-ready enterprise SaaS delivered in 8-week sprints.",
                    "display_order": 8
                },
                {
                    "slug": "ai-cybersecurity-threat-intelligence",
                    "title": "AI Cybersecurity & Threat Intelligence",
                    "short_description": "Autonomous threat detection, zero-day anomaly classification, SIEM triage agents, and LLM guardrails.",
                    "full_description": "We architect resilient AI-driven cybersecurity infrastructure for modern digital enterprises. From real-time network traffic anomaly scoring and automated SIEM alert triage to red-teaming LLM applications and automated prompt injection defense, we safeguard critical enterprise assets.",
                    "icon": "shield",
                    "deliverables": json.dumps(["Real-time anomaly detection pipelines", "SIEM & SOC automated triaging agents", "Adversarial attack & prompt injection defense", "Zero-trust access policy analyzers", "Security compliance audit reports"]),
                    "example_outcome": "99.4% precision in zero-day anomaly detection and 80% reduction in false-positive SOC alerts.",
                    "display_order": 9
                }
            ]
        for s in services_data:
            if not db.query(Service).filter(Service.slug == s["slug"]).first():
                db.add(Service(**s))
        db.commit()

        # 4. Seed Industries
        industries_data = [
                {
                    "slug": "healthcare",
                    "name": "Healthcare & Life Sciences",
                    "icon": "activity",
                    "summary": "Clinical administration assistants, compliant medical document extraction, and diagnostic image triage prototypes.",
                    "solutions_json": json.dumps([
                        "Clinical chart summarization and approved knowledge search",
                        "Radiology and dermatology image triage pipelines",
                        "Patient intake and appointment triage chatbots",
                        "HIPAA-compliant document parsing"
                    ]),
                    "considerations_json": json.dumps([
                        "Strict regulatory compliance & patient privacy controls",
                        "Mandatory human clinical oversight for diagnostic prototypes",
                        "Air-gapped deployment capability"
                    ]),
                    "display_order": 1
                },
                {
                    "slug": "finance",
                    "name": "Finance & Capital Markets",
                    "icon": "dollar-sign",
                    "summary": "Intelligent financial document parsing, transaction fraud scoring, and audit-ready automated compliance workflows.",
                    "solutions_json": json.dumps([
                        "Automated balance sheet and invoice extraction",
                        "Real-time fraud anomaly detection models",
                        "KYC and AML compliance verification assistants",
                        "Risk prediction and credit assessment scoring"
                    ]),
                    "considerations_json": json.dumps([
                        "Explainability and mathematical interpretability",
                        "Full audit logging and decision traceability",
                        "Human approval gates on all financial execution"
                    ]),
                    "display_order": 2
                },
                {
                    "slug": "education",
                    "name": "Education & EdTech",
                    "icon": "book-open",
                    "summary": "Adaptive student learning assistants, automated homework feedback, and curriculum question-answering engines.",
                    "solutions_json": json.dumps([
                        "Personalized 24/7 student tutoring agents",
                        "Automated essay scoring and rubric evaluation",
                        "Parent-facing educational progress summaries",
                        "Curriculum-aligned RAG knowledge engines"
                    ]),
                    "considerations_json": json.dumps([
                        "Age-appropriate safety and content moderation",
                        "Strict child-data privacy and consent safeguards",
                        "Teacher oversight and curriculum alignment"
                    ]),
                    "display_order": 3
                },
                {
                    "slug": "agriculture",
                    "name": "Agriculture & Agri-Tech",
                    "icon": "sun",
                    "summary": "Computer vision for crop health diagnosis, predictive yield modeling, and localized farmer advisory systems.",
                    "solutions_json": json.dumps([
                        "Smartphone photo leaf disease classification",
                        "Microclimate weather & soil moisture analytics",
                        "Yield forecasting and harvest timing copilots",
                        "Multilingual voice and text advisory agents"
                    ]),
                    "considerations_json": json.dumps([
                        "Localized climate and crop validation",
                        "Offline edge model execution on low-spec devices",
                        "Clear boundaries on agricultural advisory recommendations"
                    ]),
                    "display_order": 4
                },
                {
                    "slug": "retail",
                    "name": "Retail & E-Commerce",
                    "icon": "shopping-bag",
                    "summary": "Visual catalog search, personalized dynamic recommendations, demand forecasting, and conversational shopping assistants.",
                    "solutions_json": json.dumps([
                        "Conversational shopping copilots with cart integration",
                        "Reverse image search for product catalogs",
                        "Inventory demand and seasonal stock forecasting",
                        "Automated customer sentiment and review analysis"
                    ]),
                    "considerations_json": json.dumps([
                        "Accurate real-time inventory synchronization",
                        "Customer data privacy and cookie governance",
                        "Brand safety in generative product descriptions"
                    ]),
                    "display_order": 5
                },
                {
                    "slug": "manufacturing",
                    "name": "Manufacturing & Industry 4.0",
                    "icon": "tool",
                    "summary": "High-speed assembly line defect detection, predictive machinery maintenance, and technical documentation retrieval.",
                    "solutions_json": json.dumps([
                        "Sub-second camera-based visual defect inspection",
                        "Vibration and sensor predictive maintenance models",
                        "Interactive equipment maintenance copilots for technicians",
                        "Safety protocol monitoring via edge cameras"
                    ]),
                    "considerations_json": json.dumps([
                        "Industrial-grade real-time latency (<30ms)",
                        "Workplace safety certification compliance",
                        "Resilience to harsh factory floor lighting and conditions"
                    ]),
                    "display_order": 6
                },
                {
                    "slug": "cybersecurity-defense",
                    "name": "Cyber Security & Critical Infrastructure",
                    "icon": "shield",
                    "summary": "Autonomous Security Operations Centers (SOC), network telemetry anomaly triaging, and zero-trust verification.",
                    "solutions_json": json.dumps([
                        "Autonomous SOC alert prioritization and forensic summaries",
                        "Network flow anomaly detection and zero-day intrusion defense",
                        "AI model security hardening and prompt injection firewalls",
                        "Continuous automated vulnerability assessments"
                    ]),
                    "considerations_json": json.dumps([
                        "Strict compliance with ISO 27001, SOC 2 Type II, and NIST frameworks",
                        "Air-gapped and on-premise inference deployment to eliminate data leakage",
                        "Zero-trust tenant isolation with continuous cryptographic verification"
                    ]),
                    "display_order": 7
                }
            ]
        for ind in industries_data:
            if not db.query(Industry).filter(Industry.slug == ind["slug"]).first():
                db.add(Industry(**ind))
        db.commit()

        # 5. Seed Portfolio Projects
        if db.query(PortfolioProject).count() == 0:
            portfolio_data = [
                {
                    "slug": "omnivision-medical-triage",
                    "title": "OmniVision: Radiology Scan Prioritization Pipeline",
                    "client_name": "Apex Healthcare Systems",
                    "industry_name": "Healthcare",
                    "challenge": "Emergency radiologists faced severe backlogs reviewing hundreds of CT and X-ray studies daily.",
                    "solution": "Built a dual-stream PyTorch convolutional triage pipeline that scans DICOM images and highlights acute anomalies.",
                    "tech_stack_json": json.dumps(["PyTorch", "FastAPI", "OpenCV", "Docker", "DICOM Server"]),
                    "outcomes_json": json.dumps([
                        "62% reduction in acute scan turnaround time",
                        "97.4% sensitivity in acute finding detection",
                        "Integrated directly into existing PACS viewer"
                    ]),
                    "image_url": "/static/images/portfolio_med.jpg",
                    "is_featured": True
                },
                {
                    "slug": "finpulse-fraud-engine",
                    "title": "FinPulse: Real-Time Fraud & Automated KYC Extractor",
                    "client_name": "FinFlow Global Capital",
                    "industry_name": "Finance",
                    "challenge": "Manual customer onboarding and loan documentation review caused an average 72-hour delay.",
                    "solution": "Deployed a hybrid OCR + LayoutLM document intelligence pipeline that extracts passport, tax, and bank data.",
                    "tech_stack_json": json.dumps(["FastAPI", "LayoutLMv3", "SQLAlchemy", "Tesseract", "Celery"]),
                    "outcomes_json": json.dumps([
                        "Instant onboarding verification in under 4 seconds",
                        "99.1% document field extraction accuracy",
                        "Zero compliance violations over 12 months"
                    ]),
                    "image_url": "/static/images/portfolio_fin.jpg",
                    "is_featured": True
                },
                {
                    "slug": "agrisense-crop-classifier",
                    "title": "AgriSense: Mobile Edge Plant Pathology Copilot",
                    "client_name": "GreenTerra AgTech",
                    "industry_name": "Agriculture",
                    "challenge": "Smallholder farmers lost up to 30% of yields due to late identification of fungal infections.",
                    "solution": "Created an ultra-lightweight MobileNetV3 model packaged into an offline Android edge engine.",
                    "tech_stack_json": json.dumps(["PyTorch", "ONNX Runtime", "FastAPI", "SQLite3", "Flutter"]),
                    "outcomes_json": json.dumps([
                        "Diagnoses 42 crop diseases directly on mobile without internet",
                        "Over 35,000 active farmer consultations logged",
                        "Estimated 18% average yield recovery"
                    ]),
                    "image_url": "/static/images/portfolio_agri.jpg",
                    "is_featured": True
                }
            ]
            for p in portfolio_data:
                db.add(PortfolioProject(**p))
            db.commit()

        # 7. Seed Knowledge Base and Documents
        kb_public = db.query(KnowledgeBase).filter(KnowledgeBase.name == "CAC Innovation Enterprise Knowledge Base").first()
        if not kb_public:
            kb_public = KnowledgeBase(
                name="CAC Innovation Enterprise Knowledge Base",
                description="Verified company capabilities, architecture standards, security guidelines, and service catalog.",
                tenant_id=None,
                is_active=True
            )
            db.add(kb_public)
            db.commit()
            db.refresh(kb_public)

            doc1_content = (
                "CTRL ALT CRAC INNOVATIONS (CAC INNOVATION), founded and started in 2021, is an enterprise AI engineering firm. "
                "Our core value proposition: We design and deliver practical AI-powered applications, "
                "intelligent agents, and automation systems that help organizations improve customer experience, "
                "streamline operations, and make better use of their data. "
                "The three pillars are AI Solutions & Services, AI Products & Innovation, and Research, Development & Training. "
                "We provide full lifecycle project delivery: lead generation -> project execution -> quality review -> client delivery -> support."
            )
            doc2_content = (
                "CTRL ALT CRAC INNOVATIONS Architecture Blueprint: "
                "The tech stack is built on FastAPI, SQLAlchemy, Pydantic, and SQLite3 (PostgreSQL production-ready). "
                "The platform features 6 distinct connected roles: Super Admin, Admin/BD, Manager, Employee, Intern, and Client. "
                "Every resource operation is strictly tenant-isolated and verified by role-based access control."
            )
            for title, content in [
                ("Company Overview & 3 Pillars", doc1_content),
                ("Architecture & 6-Role System", doc2_content)
            ]:
                chunks = [content]
                db.add(KBDocument(
                    kb_id=kb_public.id,
                    title=title,
                    content_text=content,
                    chunks_json=json.dumps(chunks),
                    status="indexed"
                ))
            db.commit()

        # 8. Seed AI Provider, Model, and Agents
        provider = db.query(AIProvider).filter(AIProvider.name == "cac_internal_engine").first()
        if not provider:
            provider = AIProvider(
                name="cac_internal_engine",
                provider_type="internal",
                is_active=True
            )
            db.add(provider)
            db.commit()
            db.refresh(provider)

        model = db.query(AIModel).filter(AIModel.name == "cac-neural-v2").first()
        if not model:
            model = AIModel(
                name="cac-neural-v2",
                provider_id=provider.id,
                context_window=128000,
                is_default=True,
                cost_tier="standard"
            )
            db.add(model)
            db.commit()

        agents_data = [
            {
                "agent_code": "website_support",
                "name": "CAC Strategic Assistant",
                "description": "Answers visitor queries on AI services, calculates project quotes, and assists consultation bookings.",
                "role_mission": "Serve as front-line AI engineer for CTRL ALT CRAC INNOVATIONS.",
                "system_instructions": "You represent CTRL ALT CRAC INNOVATIONS. Guide potential clients through services and calculate project ranges.",
                "permitted_tools_json": json.dumps(["calculate_estimate", "knowledge_search", "schedule_consultation"]),
                "requires_human_approval": False,
                "is_active": True
            },
            {
                "agent_code": "project_planner",
                "name": "AI Project & Task Planner",
                "description": "Breaks down approved client project scopes into milestones, employee assignments, and supervised intern tasks.",
                "role_mission": "Generate task dependency graphs and estimated durations.",
                "system_instructions": "Analyze requirements and create structured sprint breakdowns with acceptance rubrics.",
                "permitted_tools_json": json.dumps(["generate_project_plan", "knowledge_search"]),
                "requires_human_approval": False,
                "is_active": True
            }
        ]
        for a in agents_data:
            if not db.query(AIAgent).filter(AIAgent.agent_code == a["agent_code"]).first():
                db.add(AIAgent(**a))
        db.commit()

        # 9. Seed Core Technologies (Admin can add more anytime)
        tech_data = [
            ("Python", "Backend", "High-performance programming language for backends, APIs, and ML pipelines.", "code"),
            ("FastAPI", "Backend", "Modern, high-speed Python web microservice framework with OpenAPI.", "zap"),
            ("React", "Frontend", "Component-driven user interface library for interactive dashboards.", "layout"),
            ("Node.js", "Backend", "Event-driven asynchronous JavaScript runtime for scalable services.", "server"),
            ("PostgreSQL", "Database", "Enterprise-grade ACID relational database with JSONB indexing.", "database"),
            ("Docker", "Cloud & DevOps", "Containerization platform for portable application deployments.", "box"),
            ("Kubernetes", "Cloud & DevOps", "Automated container orchestration, scaling, and load-balancing.", "cloud"),
            ("Flutter", "Mobile", "Cross-platform mobile and desktop application framework by Google.", "smartphone"),
            ("Cyber Security & PenTesting", "Cyber Security", "Defensive security, vulnerability assessment, and threat mitigation.", "shield"),
            ("AWS Cloud", "Cloud & DevOps", "Amazon Web Services cloud infrastructure, S3, and serverless compute.", "cloud"),
            ("PyTorch", "AI / ML", "Deep learning and tensor computation framework for neural architectures.", "cpu"),
            ("Next.js", "Frontend", "Server-rendered React framework for enterprise performance and SEO.", "globe")
        ]
        for t_name, t_cat, t_desc, t_icon in tech_data:
            if not db.query(Technology).filter(Technology.name == t_name).first():
                db.add(Technology(name=t_name, category=t_cat, description=t_desc, icon=t_icon))
        db.commit()

        # 10. Seed Intern Role Tracks (Admin can add more anytime)
        intern_tracks = [
            ("Python Backend Intern", "Backend", json.dumps(["Python", "FastAPI", "PostgreSQL"]), "Assigned to build RESTful microservices, database schemas, and background workers.", 3),
            ("Frontend Web Development Intern", "Frontend", json.dumps(["React", "JavaScript", "HTML/CSS"]), "Develops responsive glassmorphism web components, data tables, and interactive UI states.", 3),
            ("Mobile App Development Intern", "Mobile", json.dumps(["Flutter", "Dart", "REST APIs"]), "Builds cross-platform Android & iOS interfaces and local offline caching engines.", 3),
            ("Cyber Security & Defense Intern", "Cyber Security", json.dumps(["Cyber Security & PenTesting", "Linux", "Networking"]), "Assists in penetration testing, vulnerability scanning, and security audits.", 3),
            ("Cloud & DevOps Intern", "Cloud & DevOps", json.dumps(["Docker", "Kubernetes", "AWS Cloud"]), "Configures Docker containers, automated CI/CD test runners, and cloud clusters.", 3),
            ("Data Science Intern", "Data Science", json.dumps(["Python", "SQL", "Pandas"]), "Data cleaning, exploratory data analysis, ETL pipelines, and feature stores.", 3),
            ("QA & Test Automation Intern", "QA/Testing", json.dumps(["Python", "Pytest", "API Testing"]), "Writes end-to-end regression suites, mock API tests, and performance benchmarks.", 3)
        ]
        for title, domain, skills, desc, duration in intern_tracks:
            if not db.query(InternRoleTrack).filter(InternRoleTrack.title == title).first():
                db.add(InternRoleTrack(title=title, domain=domain, required_skills_json=skills, description=desc, duration_months=duration))
        db.commit()

        # If clean production / fresh start is requested, stop here without adding mock business data
        if not seed_demo:
            return

        # =========================================================================
        # DEMO SEED DATA (Only populated if seed_demo=True)
        # =========================================================================

        # 9. Seed Demo Clients
        client_apex = db.query(Client).filter(Client.code == "APEX-HEALTH").first()
        if not client_apex:
            client_apex = Client(
                name="Apex Healthcare Systems",
                code="APEX-HEALTH",
                industry="Healthcare",
                primary_contact_name="Dr. Elena Vance",
                primary_contact_email="elena@apexhealth.com",
                tier="Enterprise"
            )
            db.add(client_apex)
            db.commit()
            db.refresh(client_apex)

        client_finflow = db.query(Client).filter(Client.code == "FINFLOW-GLOBAL").first()
        if not client_finflow:
            client_finflow = Client(
                name="FinFlow Global Capital",
                code="FINFLOW-GLOBAL",
                industry="Finance",
                primary_contact_name="Marcus Vance",
                primary_contact_email="marcus@finflow.io",
                tier="Enterprise"
            )
            db.add(client_finflow)
            db.commit()
            db.refresh(client_finflow)

        # 10. Seed Demo Team Members
        demo_users_data = [
            ("bd@cac-innovations.com", "Bd@123456", "Rachel Adams", "Business Development Lead", "Growth", "admin", None),
            ("manager@cac-innovations.com", "Manager@123456", "Victor Ray", "Engineering Project Manager", "Delivery", "manager", None),
            ("dev@cac-innovations.com", "Dev@123456", "Alex Mercer", "Senior Full-Stack AI Engineer", "Engineering", "employee", None),
            ("intern@cac-innovations.com", "Intern@123456", "Maya Lin", "AI Engineering Fellow", "Internship", "intern", None),
            ("client@apexhealth.com", "Client@123456", "Dr. Elena Vance", "Chief Medical Officer", "Client", "client", client_apex.id)
        ]
        created_users = {}
        for email, pwd, name, title, dept, role_name, tenant_id in demo_users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    title=title,
                    department=dept,
                    role_id=roles_map[role_name].id,
                    tenant_id=tenant_id,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            created_users[role_name] = user

        # 11. Seed Projects, Milestones, and Connected Tasks
        manager_user = created_users.get("manager")
        dev_user = created_users.get("employee")
        intern_user = created_users.get("intern")

        proj = db.query(Project).filter(Project.title.like("%Clinical Document%")).first()
        if not proj:
            proj = Project(
                client_id=client_apex.id,
                manager_id=manager_user.id if manager_user else None,
                title="Clinical Document Intelligence & Triage System",
                description="HIPAA-aligned document ingestion and radiology report classification system.",
                status="in_progress",
                progress_percentage=65,
                budget="$38,000",
                repo_url="https://github.com/cac-innovations/apex-clinical-intelligence",
                target_delivery_date=datetime.now(timezone.utc) + timedelta(days=45)
            )
            db.add(proj)
            db.commit()
            db.refresh(proj)

            m1 = Milestone(
                project_id=proj.id,
                title="Phase 1: Architecture & Data Ingestion Specification",
                deliverables="Signed architecture doc & mock endpoints",
                status="completed",
                invoice_amount=9500.0,
                due_date=datetime.now(timezone.utc) - timedelta(days=15)
            )
            m2 = Milestone(
                project_id=proj.id,
                title="Phase 2: PyTorch Model Training & DICOM Validation",
                deliverables="Model weights & ROC-AUC evaluation report",
                status="completed",
                invoice_amount=12000.0,
                due_date=datetime.now(timezone.utc) - timedelta(days=5)
            )
            m3 = Milestone(
                project_id=proj.id,
                title="Phase 3: FastAPI Backend & RAG Security Integration",
                deliverables="REST API with role-based JWT isolation",
                status="in_progress",
                invoice_amount=9500.0,
                due_date=datetime.now(timezone.utc) + timedelta(days=20)
            )
            db.add_all([m1, m2, m3])
            db.commit()
            db.refresh(m3)

            # Seed Tasks connecting Manager -> Employee -> Intern
            t1 = Task(
                project_id=proj.id,
                milestone_id=m3.id,
                title="Build Tenant-Isolated RAG Vector Store & BM25 Ranker",
                description="Implement text normalization and sliding window chunking. Ensure queries strictly filter by tenant_id.",
                assigned_to_id=dev_user.id if dev_user else None,
                created_by_id=manager_user.id if manager_user else None,
                approved_by_id=manager_user.id if manager_user else None,
                priority="High",
                status="Completed",
                repo_url="https://github.com/cac-innovations/apex-clinical-intelligence",
                pr_url="https://github.com/cac-innovations/apex-clinical-intelligence/pull/12",
                submission_notes="Completed BM25 ranking algorithm with 100% test pass on tenant boundaries.",
                review_feedback="Approved by Victor Ray (Manager). Great code quality."
            )
            t2 = Task(
                project_id=proj.id,
                milestone_id=m3.id,
                title="Build DICOM Metadata Extraction & Preprocessing Pipeline",
                description="Develop Python script to parse DICOM header tags (PatientID, StudyDate, Modality) into sanitized JSON format.",
                assigned_to_id=intern_user.id if intern_user else None,
                created_by_id=dev_user.id if dev_user else None,
                priority="Medium",
                status="Under Review",
                repo_url="https://github.com/cac-innovations/apex-clinical-intelligence",
                branch_name="feature/dicom-tags",
                pr_url="https://github.com/cac-innovations/apex-clinical-intelligence/pull/18",
                submission_notes="Parsed 45 test studies. All tags match DICOM standard. Ready for review.",
                review_feedback="Under review by Alex Mercer (Senior Dev) and Victor Ray (Manager)."
            )
            t3 = Task(
                project_id=proj.id,
                milestone_id=m3.id,
                title="Frontend Glassmorphism Triage Dashboard & DICOM Viewer Integration",
                description="Connect PACS study triage list to HTML table with priority badges and real-time status updates.",
                assigned_to_id=intern_user.id if intern_user else None,
                created_by_id=manager_user.id if manager_user else None,
                priority="Medium",
                status="Assigned",
                repo_url="https://github.com/cac-innovations/apex-clinical-intelligence",
                branch_name="feature/triage-ui"
            )
            db.add_all([t1, t2, t3])
            db.commit()

            # Seed Invoices
            inv1 = Invoice(
                invoice_number="INV-2026-001",
                client_id=client_apex.id,
                project_id=proj.id,
                milestone_id=m1.id,
                amount=9500.0,
                status="paid",
                paid_at=datetime.now(timezone.utc) - timedelta(days=10)
            )
            inv2 = Invoice(
                invoice_number="INV-2026-002",
                client_id=client_apex.id,
                project_id=proj.id,
                milestone_id=m2.id,
                amount=12000.0,
                status="sent",
                due_date=datetime.now(timezone.utc) + timedelta(days=15)
            )
            db.add_all([inv1, inv2])
            db.commit()

            # Seed Notifications
            if intern_user:
                db.add(Notification(
                    user_id=intern_user.id,
                    title="Task Assigned",
                    message="You have been assigned: 'Build DICOM Metadata Extraction Pipeline'.",
                    link="/intern#tasks",
                    notification_type="task_assignment"
                ))
            if manager_user:
                db.add(Notification(
                    user_id=manager_user.id,
                    title="Work Submitted For Review",
                    message="Maya Lin submitted PR #18 for task 'Build DICOM Metadata Extraction Pipeline'.",
                    link="/manager#reviews",
                    notification_type="task_submitted"
                ))
            db.commit()

        # 10. Seed Intern Cohort
        if db.query(InternBatch).count() == 0:
            batch = InternBatch(
                batch_name="Cohort 2026-Q1 AI Engineering",
                track="Enterprise Full-Stack & Generative AI",
                start_date=datetime.now(timezone.utc) - timedelta(days=30),
                end_date=datetime.now(timezone.utc) + timedelta(days=60),
                mentor_name="Alex Mercer (Tech Lead)"
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

            task_intern = InternTask(
                batch_id=batch.id,
                title="Module 1: Responsive Public UI with Glassmorphism Components",
                track="UI Integration",
                description="Implement responsive navigation, accessible form controls, and theme tokens matching CAC violet-cyan aesthetics.",
                acceptance_criteria="Fully mobile-responsive, zero console errors, semantic HTML5.",
                difficulty="Intermediate"
            )
            db.add(task_intern)
            db.commit()

            if intern_user:
                sub = InternSubmission(
                    task_id=task_intern.id,
                    intern_id=intern_user.id,
                    repo_url="https://github.com/cac-fellowship/intern-ui-showcase",
                    demo_url="https://ui-preview.cac-innovations.internal",
                    notes="Completed responsive layout and chat drawer.",
                    status="approved",
                    score=95,
                    mentor_feedback="Superb code organization and clean dark-mode styling."
                )
                db.add(sub)
                db.commit()

        # 11. Seed CRM Leads in different stages
        if db.query(Enquiry).count() == 0:
            db.add(Enquiry(
                name="Sarah Jenkins",
                email="s.jenkins@novatech-logistics.com",
                company="NovaTech Logistics",
                industry="Manufacturing",
                service_interest="Autonomous AI Agent Workflows",
                budget="$25k - $50k",
                timeline="1 month",
                message="We are looking to automate our multi-facility bill of lading cross-referencing using an autonomous agent.",
                status="requirement_discussion",
                assigned_to="Rachel Adams (BD Lead)",
                lead_score=85,
                qualification_notes="High value manufacturing lead. Budget $25k-$50k, 1 month timeline."
            ))
            db.add(Enquiry(
                name="David Chen",
                email="david@finflow-global.com",
                company="FinFlow Global Capital",
                industry="Finance",
                service_interest="NLP & Generative AI",
                budget="$30k - $75k",
                timeline="Immediate (1-2 weeks)",
                message="Automated balance sheet and invoice extraction pipeline.",
                status="won",
                assigned_to="Rachel Adams (BD Lead)",
                lead_score=92,
                qualification_notes="Proposal approved and signed. Ready for project kick-off."
            ))
            db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    print("Database re-initialized with 6 roles, connected workflow, tasks, invoices, and notifications!")
