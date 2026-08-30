from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import (
    routes_agents,
    routes_gateway,
    routes_governance,
    routes_hub,
    routes_mcp,
    routes_ops,
    routes_rag,
    routes_views,
    routes_workspace,
)
from app.config import get_settings
from app.db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    worker = None
    if settings.event_worker_enabled:
        from app.worker import get_worker

        worker = get_worker()
        worker.start()
    yield
    if worker:
        worker.stop()


openapi_tags = [
    {"name": "hub", "description": "Single Source of Truth (SSOT). Manage customers, products, employees, orders, and A/S tickets."},
    {"name": "rag", "description": "Enterprise Document Ingestion & RAG Vector Search (Server-side ACL Security Trimming)."},
    {"name": "ai-gateway", "description": "Provider-agnostic LLM Gateway Abstraction Layer."},
    {"name": "ops", "description": "SaaS Orchestration, Transactional Outbox Worker, and Health Probes."},
    {"name": "agents", "description": "Governed Multi-Agent Subsystem (Triage, Knowledge, Follow-up, Reconcile, Evolve)."},
    {"name": "views", "description": "Read-only operational rollups computed from SSOT hub events."},
    {"name": "workspace", "description": "Role-Based Workspace Layout and Experience Layer."},
    {"name": "governance", "description": "Manager-Only Audit Logs, Adoption KPIs, and Data Ownership Policies."},
    {"name": "mcp", "description": "Model Context Protocol (MCP) JSON-RPC Tool Registry."},
]

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Unified Ops AX — Autonomous Fleet Telemetry & Governed Multi-Agent Monolith",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)


import os
from fastapi.responses import FileResponse, HTMLResponse

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for candidate in ["dashboard.html", "unified_ops_ax_dashboard.html", "web/index.html"]:
        path = os.path.join(base_dir, candidate)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Unified Ops AX — Google Cloud Run Backend Active</h1><p>Preflight: <a href='/ops/preflight'>/ops/preflight</a> | Health: <a href='/health'>/health</a></p>")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.default_llm_provider,
        "embedding_provider": settings.embedding_provider,
        "vector_backend": settings.vector_backend,
    }


app.include_router(routes_hub.router)
app.include_router(routes_rag.router)
app.include_router(routes_gateway.router)
app.include_router(routes_ops.router)
app.include_router(routes_agents.router)
app.include_router(routes_views.router)
app.include_router(routes_workspace.router)
app.include_router(routes_governance.router)
app.include_router(routes_mcp.router)
