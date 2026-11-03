# CTRL ALT CRAC INNOVATIONS (CAC INNOVATION)
## Operations & Platform User Guide: Integrated Business Management & AI Delivery Platform

---

### Table of Contents
1. [Platform Overview & Philosophy](#1-platform-overview--philosophy)
2. [Role Hierarchy & Security Matrix](#2-role-hierarchy--security-matrix)
3. [Starting the Application](#3-starting-the-application)
4. [Initial Super Admin Setup & User Provisioning](#4-initial-super-admin-setup--user-provisioning)
5. [End-to-End Business Delivery Workflow](#5-end-to-end-business-delivery-workflow)
   - [Phase 1: Inbound Lead Generation & Scoring (Public / CRM)](#phase-1-inbound-lead-generation--scoring-public--crm)
   - [Phase 2: Lead Qualification & Project Onboarding (Admin / BD)](#phase-2-lead-qualification--project-onboarding-admin--bd)
   - [Phase 3: Project Scoping, Milestones & Task Delegation (Manager)](#phase-3-project-scoping-milestones--task-delegation-manager)
   - [Phase 4: Engineering Execution & Intern Mentorship (Employee / Developer)](#phase-4-engineering-execution--intern-mentorship-employee--developer)
   - [Phase 5: Submissions, Review Gates & Approvals (Intern & Manager)](#phase-5-submissions-review-gates--approvals-intern--manager)
   - [Phase 6: Client Approvals, Invoicing & Delivery (Client Workspace)](#phase-6-client-approvals-invoicing--delivery-client-workspace)
6. [Role-Scoped AI Assistants & RAG Knowledge Retrieval](#6-role-scoped-ai-assistants--rag-knowledge-retrieval)
7. [API Endpoints & Integration Guide](#7-api-endpoints--integration-guide)
8. [Database Maintenance & Reset Protocol](#8-database-maintenance--reset-protocol)

---

### 1. Platform Overview & Philosophy

**CTRL ALT CRAC INNOVATIONS (CAC INNOVATION)**, started in 2021, operates not merely as an informational corporate website, but as a fully unified **Enterprise AI Operations and Service Delivery Platform**. 

Instead of isolating tools across disjointed SaaS apps (separate CRM, separate Jira/Trello, separate Slack, separate LMS, separate invoicing), CAC unites the entire firm into a single operational loop:
- **Public & Prospective Clients** discover AI offerings, estimate scopes via an intelligent quotation engine, and submit technical briefs.
- **Business Development & Admins** qualify leads through automated budget-authority-need (BANT) scoring and onboard accounts with one click.
- **Project Managers** allocate engineering sprints, balance developer and intern workloads, and enforce dependency gates.
- **Engineers & Developers** implement AI solutions, mentor junior talent, submit PR references, and conduct technical reviews.
- **Interns** receive structured task briefs, complete hands-on learning assignments, and submit code with mentorship feedback loops.
- **Clients** monitor real-time milestone progress, review delivered artifacts, pay invoices, and raise priority support tickets.

---

### 2. Role Hierarchy & Security Matrix

The system enforces strict role-based access control (RBAC) across six distinct user tiers:

| Role Name | Scope | Core Responsibilities & Capabilities |
| :--- | :--- | :--- |
| **Super Admin** | System-Wide | Full configuration, tenant oversight, user account creation, system auditing, billing & global settings. |
| **Admin / BD** | Business & Sales | Lead scoring, client onboarding, quotation generation, initial project creation, invoicing & contracts. |
| **Manager** | Delivery & Sprints | Project architecture, sprint planning, task & intern delegation, deadline tracking, QA gates & final approvals. |
| **Employee / Dev** | Engineering | Production code, model training, task execution, intern task assignment, technical reviews & documentation. |
| **Intern** | Learning & Dev | Execution of assigned sandbox/production tasks, pull request submissions, learning milestones & feedback logging. |
| **Client** | Project Workspace | Transparent milestone progress, sprint reviews, deliverable approvals, invoice tracking & support desk. |

---

### 3. Starting the Application

#### Prerequisites
- **Python 3.10+** (Python 3.14 verified)
- Dependencies installed from `requirements.txt`:
  ```bash
  pip install fastapi uvicorn sqlalchemy pydantic jinja2 python-jose passlib bcrypt python-multipart
  ```

#### Launch Command
To launch the FastAPI server with live auto-reloading:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Access Points
- **Public Website & Discovery Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Unified Login Portal**: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Technical Specification**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 4. Initial Executive Setup & User Provisioning

When launching with a fresh database, root executive accounts are pre-configured:
- **Super Admin**: `admin@cac-innovations.com` / `Admin@123456` (Admin Console: `/admin`)
- **Executive CEO**: `ceo@cac-innovations.com` / `Ceo@123456` (Dedicated Gateway: `/ceo`)

#### Executive CEO Security & Standard Portal Governance:
- **Dedicated CEO Gateway**: Executive Leadership must log in exclusively at [`http://127.0.0.1:8000/ceo`](http://127.0.0.1:8000/ceo).
- **1st Attempt on `/login` (Warning)**: If CEO credentials are submitted on the standard staff login page, access is halted and an **Amber Warning** is displayed directing them to `/ceo`.
- **2nd Attempt on `/login` (Security Alert)**: If CEO credentials are submitted again on `/login`, a **High-Priority Security Alert** is triggered and recorded in the audit trail, locking out standard login attempts.
- **Mandatory Role Type Selection**: All staff logging in at `/login` must choose their assigned role (`intern`, `employee`, `manager`, `admin`, `client`). The backend validates that the account matches the selected role.

#### Step 4.1: Log in as Super Admin or CEO
1. For Admin operations: Navigate to `http://127.0.0.1:8000/login` (select `Admin / Business Development`).
2. For Executive CEO oversight: Navigate to `http://127.0.0.1:8000/ceo`.
3. You will be routed to your respective command center.

#### Step 4.2: Provision Employee Credentials (No Default Accounts)
There are **zero default employee credentials** in the system. The Super Admin creates credentials for every team member directly from the **Admin Portal** (`/admin`):
1. In the **Employee & Team Credential Provisioning** panel, click **`+ Provision New Employee Account`**.
2. Fill in the team member's details:
   - **Full Name** (e.g. `Alex Mercer`)
   - **Company Email** (e.g. `alex@cac-innovations.com`)
   - **Initial Password** (or click `Generate`)
   - **System Role**:
     - `manager` (Project Manager — sprint planning, task assignments, review gates)
     - `employee` (Developer / AI Engineer — code implementation, intern task delegation)
     - `intern` (AI Engineering Fellow — assigned tasks, PR code submissions)
     - `admin` (Business Development — CRM leads, quotations, onboarding)
     - `client` (Client Organization — milestone tracking, deliverables, invoices)
   - **Job Title & Department** (e.g., `Lead AI Engineer`, `Applied Engineering`)
3. Click **Create & Issue Credentials**. The employee can immediately log in at `/login` with their credentials.

Alternatively, provisioning can be done programmatically:
```json
POST /api/v1/auth/users
{
  "email": "alex@cac-innovations.com",
  "full_name": "Alex Mercer",
  "password": "SecurePassword@2026",
  "role_name": "employee",
  "title": "Senior AI Engineer",
  "department": "Applied Engineering"
}
```

---

### 5. End-to-End Business Delivery Workflow

Here is how real customer projects move seamlessly through the 6-role lifecycle:

```
[ Prospective Client ]
       │
       ▼  (Fills Contact / AI Scoping Form)
[ Public Lead Captured ] ──► Automated AI Scoring (0-100)
                                      │
                                      ▼
[ Admin / BD Portal ] ────► Qualifies Lead & Clicks "Convert to Client & Project"
                                      │
                                      ▼
[ Project Manager Portal ] ──► Breaks down Milestones & Creates Dependent Tasks
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
      [ Employee / Developer ]                  [ Intern Sandbox / Tasks ]
       - Builds core model pipelines             - Data preprocessing & tests
       - Mentors interns                         - Submits PR for review
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
             [ Manager Review & Quality Approval Gate ]
                                      │
                                      ▼
[ Client Portal ] ──────────► Views Milestones, Reviews Deliverables,
                              Approves Completion & Settles Invoices
```

#### Phase 1: Inbound Lead Generation & Scoring (Public / CRM)
- Clients visit the public site:
  - Explore **Enterprise AI Services** (`/services`), **Industry Verticals** (`/industries`), and **Case Studies** (`/portfolio`).
  - Use the **Interactive AI Chat Widget** or **Contact & Quotation Form** (`/contact`).
- Submissions automatically calculate an **AI Lead Score (0–100)**:
  - Considers budget tier, timeline, technical readiness, and decision-maker status.
  - Automatically flags leads as `HOT`, `WARM`, or `COLD`.

#### Phase 2: Lead Qualification & Project Onboarding (Admin / BD)
- **Role**: `admin` or `super_admin` (`/portal/admin`)
- Review incoming leads in the CRM table.
- Click **"Convert to Client & Create Project"**:
  - Automatically provisions a **Client Organization Record** with custom client code (e.g. `CLT-NEXUS-01`).
  - Generates a **Client Portal Account** for the stakeholder.
  - Initializes a new **Project Workspace** linked to the client with initial budget, deadline, and scope.

#### Phase 3: Project Scoping, Milestones & Task Delegation (Manager)
- **Role**: `manager` (`/portal/manager`)
- Assign the engineering lead (`employee`) and set sprint milestones:
  - Milestone 1: *Data Preparation & Exploratory Analysis*
  - Milestone 2: *Model Fine-Tuning & Evaluation*
  - Milestone 3: *FastAPI Microservice & Cloud Deployment*
- Create individual tasks with:
  - **Priority**: `Critical`, `High`, `Medium`, `Low`.
  - **Task Dependency**: Link prerequisite tasks (e.g., Task #2 cannot start until Task #1 is Approved).
  - **Estimated Hours** & **Due Date**.

#### Phase 4: Engineering Execution & Intern Mentorship (Employee / Developer)
- **Role**: `employee` (`/portal/employee`)
- Developers view their assigned sprint tasks in their personal workbench.
- When an engineering task has subcomponents suitable for training or assistance:
  - The developer creates an **Intern Task** (e.g., *"Clean and tokenize 5,000 biomedical abstracts"*).
  - Assigns it to an onboarding intern with specific guidelines, branch name, and repository URL.
- Developers update their status: `Backlog` ➔ `In Progress` ➔ `Under Review`.

#### Phase 5: Submissions, Review Gates & Approvals (Intern & Manager)
- **Role**: `intern` (`/portal/intern`)
  - Intern views assigned learning tasks, instructions, and target deadlines.
  - Submits work by linking code PR, documentation link, and personal reflection.
- **Review Cycle**:
  - **Employee/Mentor** conducts initial technical review (`Request Changes` or `Recommend Approval`).
  - **Project Manager** verifies acceptance criteria and marks task `Approved` / `Completed`.

#### Phase 6: Client Approvals, Invoicing & Delivery (Client Workspace)
- **Role**: `client` (`/portal/client`)
- The client logs into their dedicated, clean dashboard:
  - **Milestone Tracker**: Visual progress bar showing real-time sprint completion.
  - **Deliverables**: Secure links to inspect delivered models, dashboards, and staging APIs.
  - **Financials & Invoices**: View itemized invoices, payment terms, and status (`Unpaid`, `Paid`).
  - **Support Desk**: Submit tickets directly to the project team with immediate manager routing.

---

### 6. Role-Scoped AI Assistants & RAG Knowledge Retrieval

CAC Innovation includes a contextual AI agent architecture. Each role has access to specialized assistants configured with custom system prompts and document context:

1. **Client Support & Scoping Agent**: Helps prospective clients identify suitable AI architectures and estimate project budgets.
2. **Sales & BD Co-Pilot**: Drafts formal proposals, summaries of customer pain points, and quotation scopes.
3. **Engineering & Architecture Advisor**: Provides architecture recommendations, FastAPI boilerplates, and RAG optimization strategies.
4. **Intern Learning Mentor**: Explains machine learning concepts, PyTorch fundamentals, and debugging advice without writing complete solutions for them.

#### Vector/Keyword RAG Search
Knowledge documents ingested via `/api/v1/knowledge-bases` are indexed for semantic and keyword search, enabling the assistant to cite proprietary CAC methodologies and blueprints.

---

### 7. API Endpoints & Integration Guide

The backend provides complete programmatic control through RESTful endpoints:

| Domain | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/token` | OAuth2 password bearer token exchange |
| **Auth** | `GET` | `/api/v1/auth/me` | Fetch active user identity and role |
| **CRM** | `POST` | `/api/v1/enquiries/` | Public inquiry submission with AI scoring |
| **CRM** | `GET` | `/api/v1/enquiries/` | List all inquiries (Admin / Manager) |
| **Projects** | `POST` | `/api/v1/projects/` | Create a new project workspace |
| **Projects** | `POST` | `/api/v1/projects/convert-lead` | Convert lead to client & active project |
| **Tasks** | `POST` | `/api/v1/projects/{id}/tasks` | Create task with dependencies & role assignment |
| **Tasks** | `PUT` | `/api/v1/projects/tasks/{id}/status` | Transition task state through review gates |
| **Interns** | `POST` | `/api/v1/interns/tasks/{id}/submit` | Submit code review & artifact link |
| **Interns** | `POST` | `/api/v1/interns/submissions/{id}/review` | Grade & approve intern submission |
| **AI / RAG** | `POST` | `/api/v1/agents/chat` | Query role-scoped AI assistants |
| **AI / RAG** | `POST` | `/api/v1/knowledge-bases/search` | Search RAG index across internal blueprints |

---

### 8. Database Maintenance & Reset Protocol

The platform runs on a high-efficiency SQLite3 database (`cac_innovations.db`) with foreign key constraints and WAL mode enabled.

#### Resetting to a Clean State
If you ever wish to purge all test data and restart fresh with only the root Super Admin:
```bash
python reset_db.py
```
This utility:
- Truncates all transactional tables (`tasks`, `projects`, `clients`, `enquiries`, `invoices`, `intern_submissions`, `audit_logs`).
- Preserves the root Super Admin (`admin@cac-innovations.com`).
- Preserves foundational role definitions and service catalog templates.
- Performs an SQLite `VACUUM` to reclaim disk space.

---
**CTRL ALT CRAC INNOVATIONS** — *Where Intelligence Meets Execution.*
