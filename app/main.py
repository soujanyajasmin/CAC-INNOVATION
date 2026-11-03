from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.init_db import init_database
from app.routers import (
    auth, services, industries, portfolio, enquiries,
    clients, projects, agents, knowledge_bases, interns, technologies, web
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CTRL ALT CRAC INNOVATIONS (CAC INNOVATION) - Enterprise AI Platform, Agent Workflows, RAG Intelligence & API Services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API Routers under /api/v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(services.router, prefix=settings.API_V1_STR)
app.include_router(industries.router, prefix=settings.API_V1_STR)
app.include_router(portfolio.router, prefix=settings.API_V1_STR)
app.include_router(enquiries.router, prefix=settings.API_V1_STR)
app.include_router(clients.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(agents.router, prefix=settings.API_V1_STR)
app.include_router(knowledge_bases.router, prefix=settings.API_V1_STR)
app.include_router(interns.router, prefix=settings.API_V1_STR)
app.include_router(technologies.router, prefix=settings.API_V1_STR)

# Web Browser Jinja2 Router
app.include_router(web.router)

@app.on_event("startup")
def startup_event():
    init_database(seed_demo=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
