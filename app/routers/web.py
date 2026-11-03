import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.permissions import get_current_user_optional
from app.models.content import Service, Industry, PortfolioProject, Enquiry
from app.models.client_project import (
    Client, Project, Milestone, Task, TaskComment,
    Notification, Invoice, SupportTicket, ProjectDocument
)
from app.models.ai import AIAgent, KnowledgeBase, KBDocument, AIUsageLog
from app.models.intern import InternBatch, InternTask, InternSubmission
from app.models.audit import AuditLog
from app.models.user import User, Role
from app.models.technology import Technology, InternRoleTrack

router = APIRouter(tags=["Web Pages"])
templates = Jinja2Templates(directory="app/templates")

def from_json(val):
    if not val:
        return []
    try:
        return json.loads(val)
    except Exception:
        return [val]

templates.env.filters["from_json"] = from_json

@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    services = db.query(Service).filter(Service.is_active == True).order_by(Service.display_order.asc()).limit(6).all()
    industries = db.query(Industry).filter(Industry.is_active == True).order_by(Industry.display_order.asc()).all()
    featured_projects = db.query(PortfolioProject).filter(PortfolioProject.is_featured == True).limit(3).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "services": services,
            "industries": industries,
            "portfolio": featured_projects
        }
    )

@router.get("/about", response_class=HTMLResponse)
def about(request: Request, user: User = Depends(get_current_user_optional)):
    return templates.TemplateResponse(request=request, name="about.html", context={"user": user})

@router.get("/services", response_class=HTMLResponse)
def services_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    services = db.query(Service).filter(Service.is_active == True).order_by(Service.display_order.asc()).all()
    return templates.TemplateResponse(request=request, name="services.html", context={"user": user, "services": services})

@router.get("/industries", response_class=HTMLResponse)
def industries_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    industries = db.query(Industry).filter(Industry.is_active == True).order_by(Industry.display_order.asc()).all()
    return templates.TemplateResponse(request=request, name="industries.html", context={"user": user, "industries": industries})

@router.get("/products", response_class=HTMLResponse)
def products_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    agents = db.query(AIAgent).filter(AIAgent.is_active == True).all()
    return templates.TemplateResponse(request=request, name="products.html", context={"user": user, "agents": agents})

@router.get("/portfolio", response_class=HTMLResponse)
def portfolio_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    projects = db.query(PortfolioProject).order_by(PortfolioProject.id.desc()).all()
    return templates.TemplateResponse(request=request, name="portfolio.html", context={"user": user, "portfolio": projects})

@router.get("/training", response_class=HTMLResponse)
def training_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    batches = db.query(InternBatch).filter(InternBatch.is_active == True).all()
    return templates.TemplateResponse(request=request, name="training.html", context={"user": user, "batches": batches})

@router.get("/contact", response_class=HTMLResponse)
def contact_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    services = db.query(Service).filter(Service.is_active == True).all()
    industries = db.query(Industry).filter(Industry.is_active == True).all()
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={"user": user, "services": services, "industries": industries}
    )

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: User = Depends(get_current_user_optional)):
    if user and user.role:
        if user.role.name in ["super_admin", "admin"]:
            return RedirectResponse(url="/admin")
        elif user.role.name == "manager":
            return RedirectResponse(url="/manager")
        elif user.role.name == "employee":
            return RedirectResponse(url="/employee")
        elif user.role.name == "client":
            return RedirectResponse(url="/client")
        elif user.role.name == "intern":
            return RedirectResponse(url="/intern")
    return templates.TemplateResponse(request=request, name="login.html", context={"user": user})

@router.get("/portal")
def portal_redirect(user: User = Depends(get_current_user_optional)):
    if not user or not user.role:
        return RedirectResponse(url="/login")
    role = user.role.name
    if role in ["super_admin", "admin"]:
        return RedirectResponse(url="/admin")
    elif role == "manager":
        return RedirectResponse(url="/manager")
    elif role == "employee":
        return RedirectResponse(url="/employee")
    elif role == "intern":
        return RedirectResponse(url="/intern")
    elif role == "client":
        return RedirectResponse(url="/client")
    return RedirectResponse(url="/")

# 0. Dedicated Executive CEO Portal
@router.get("/ceo", response_class=HTMLResponse)
def ceo_portal(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    is_authenticated_ceo = False
    if user and user.role and user.role.name == "super_admin":
        is_authenticated_ceo = True
    elif user and user.title and ("ceo" in user.title.lower() or "chief executive" in user.title.lower()):
        is_authenticated_ceo = True

    enquiries = db.query(Enquiry).order_by(Enquiry.created_at.desc()).all()
    clients = db.query(Client).all()
    projects = db.query(Project).all()
    all_users = db.query(User).all()
    invoices = db.query(Invoice).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()

    # Calculate gross deal pipeline
    total_pipeline_val = sum(inv.amount for inv in invoices if inv.amount)
    for p in projects:
        try:
            val_clean = float("".join(c for c in p.budget if c.isdigit() or c == "."))
            total_pipeline_val += val_clean
        except (ValueError, TypeError):
            total_pipeline_val += 25000.0

    return templates.TemplateResponse(
        request=request,
        name="ceo_portal.html",
        context={
            "user": user,
            "is_authenticated_ceo": is_authenticated_ceo,
            "enquiries": enquiries,
            "clients": clients,
            "projects": projects,
            "all_users": all_users,
            "invoices": invoices,
            "total_pipeline_val": total_pipeline_val,
            "audit_logs": audit_logs
        }
    )

# 1. Admin & BD Portal
@router.get("/admin", response_class=HTMLResponse)
def admin_portal(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    if not user or not user.role or user.role.name not in ["super_admin", "admin"]:
        return RedirectResponse(url="/login?msg=Please+log+in+as+Admin")
    
    enquiries = db.query(Enquiry).order_by(Enquiry.created_at.desc()).all()
    clients = db.query(Client).all()
    projects = db.query(Project).all()
    managers = db.query(User).join(User.role).filter(User.role.has(name="manager")).all()
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(15).all()
    agents = db.query(AIAgent).all()
    knowledge_bases = db.query(KnowledgeBase).all()
    audit_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(15).all()
    all_users = db.query(User).order_by(User.id.desc()).all()
    roles = db.query(Role).all()
    technologies = db.query(Technology).filter(Technology.is_active == True).order_by(Technology.category.asc(), Technology.name.asc()).all()
    intern_roles = db.query(InternRoleTrack).filter(InternRoleTrack.is_active == True).order_by(InternRoleTrack.id.asc()).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_portal.html",
        context={
            "user": user,
            "enquiries": enquiries,
            "clients": clients,
            "projects": projects,
            "managers": managers,
            "invoices": invoices,
            "agents": agents,
            "knowledge_bases": knowledge_bases,
            "audit_logs": audit_logs,
            "all_users": all_users,
            "roles": roles,
            "technologies": technologies,
            "intern_roles": intern_roles
        }
    )

# 2. Manager Portal
@router.get("/manager", response_class=HTMLResponse)
def manager_portal(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    if not user or not user.role or user.role.name not in ["super_admin", "admin", "manager"]:
        return RedirectResponse(url="/login?msg=Please+log+in+as+Manager")
    
    # Manager assigned clients & projects
    if user.role.name in ["super_admin", "admin"]:
        my_clients = db.query(Client).all()
        projects = db.query(Project).all()
    else:
        my_clients = db.query(Client).filter(Client.manager_id == user.id).all()
        projects = db.query(Project).filter((Project.manager_id == user.id) | (Project.client.has(manager_id=user.id))).all()

    tasks_waiting_review = db.query(Task).filter(Task.status == "Under Review").all()
    all_tasks = db.query(Task).order_by(Task.due_date.asc()).all()
    
    # Team members available for assignment (employees and interns)
    employees = db.query(User).join(User.role).filter(User.role.has(name="employee")).all()
    interns = db.query(User).join(User.role).filter(User.role.has(name="intern")).all()
    notifications = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(10).all()

    return templates.TemplateResponse(
        request=request,
        name="manager_portal.html",
        context={
            "user": user,
            "clients": my_clients,
            "projects": projects,
            "tasks_waiting_review": tasks_waiting_review,
            "all_tasks": all_tasks,
            "employees": employees,
            "interns": interns,
            "notifications": notifications
        }
    )

# 3. Employee / Developer Portal
@router.get("/employee", response_class=HTMLResponse)
def employee_portal(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    if not user or not user.role or user.role.name not in ["super_admin", "admin", "manager", "employee"]:
        return RedirectResponse(url="/login?msg=Please+log+in+as+Developer")
    
    my_tasks = db.query(Task).filter(Task.assigned_to_id == user.id).all()
    all_projects = db.query(Project).all()
    interns = db.query(User).join(User.role).filter(User.role.has(name="intern")).all()
    notifications = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(10).all()

    return templates.TemplateResponse(
        request=request,
        name="employee_portal.html",
        context={
            "user": user,
            "my_tasks": my_tasks,
            "projects": all_projects,
            "interns": interns,
            "notifications": notifications
        }
    )

# 4. Client Portal
@router.get("/client", response_class=HTMLResponse)
def client_portal(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    if not user or not user.role or user.role.name not in ["client", "super_admin", "admin"]:
        return RedirectResponse(url="/login?msg=Please+log+in+with+client+credentials")
    
    tenant_id = user.tenant_id
    if not tenant_id and user.role.name in ["super_admin", "admin"]:
        first_client = db.query(Client).first()
        tenant_id = first_client.id if first_client else None
        
    client = db.query(Client).filter(Client.id == tenant_id).first() if tenant_id else None
    projects = db.query(Project).filter(Project.client_id == tenant_id).all() if tenant_id else []
    invoices = db.query(Invoice).filter(Invoice.client_id == tenant_id).all() if tenant_id else []
    tickets = db.query(SupportTicket).filter(SupportTicket.client_id == tenant_id).order_by(SupportTicket.created_at.desc()).all() if tenant_id else []
    kb = db.query(KnowledgeBase).filter((KnowledgeBase.tenant_id == tenant_id) | (KnowledgeBase.tenant_id == None)).all()

    return templates.TemplateResponse(
        request=request,
        name="client_portal.html",
        context={
            "user": user,
            "client": client,
            "projects": projects,
            "invoices": invoices,
            "tickets": tickets,
            "knowledge_bases": kb
        }
    )

# 5. Intern Portal
@router.get("/intern", response_class=HTMLResponse)
def intern_portal(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
    if not user or not user.role or user.role.name not in ["intern", "employee", "manager", "super_admin", "admin"]:
        return RedirectResponse(url="/login?msg=Please+log+in+with+intern+account")
    
    # Intern assigned tasks from projects
    my_tasks = db.query(Task).filter(Task.assigned_to_id == user.id).all()
    batches = db.query(InternBatch).all()
    module_tasks = db.query(InternTask).all()
    submissions = db.query(InternSubmission).filter(InternSubmission.intern_id == user.id).all() if user.role.name == "intern" else db.query(InternSubmission).all()
    notifications = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(10).all()

    return templates.TemplateResponse(
        request=request,
        name="intern_portal.html",
        context={
            "user": user,
            "my_tasks": my_tasks,
            "batches": batches,
            "tasks": module_tasks,
            "submissions": submissions,
            "notifications": notifications
        }
    )
