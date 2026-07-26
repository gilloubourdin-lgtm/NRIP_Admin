from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import PROJECT_ROOT, get_settings
from app.services.catalog_service import (
    build_catalog_summary,
    scan_nrip_documents,
)


router = APIRouter()

templates = Jinja2Templates(
    directory=str(PROJECT_ROOT / "app" / "templates")
)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    settings = get_settings()

    documents = scan_nrip_documents(settings.nrip_root)
    summary = build_catalog_summary(documents)

    recent_documents = sorted(
        documents,
        key=lambda item: item.modified_at,
        reverse=True,
    )[:8]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "summary": summary,
            "recent_documents": recent_documents,
        },
    )