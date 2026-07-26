from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import PROJECT_ROOT, get_settings
from app.services.catalog_service import scan_nrip_documents


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

templates = Jinja2Templates(
    directory=str(PROJECT_ROOT / "app" / "templates")
)


@router.get("/", response_class=HTMLResponse)
def document_catalog(request: Request):
    settings = get_settings()
    documents = scan_nrip_documents(settings.nrip_root)

    return templates.TemplateResponse(
        request=request,
        name="documents/list.html",
        context={
            "documents": documents,
            "document_count": len(documents),
        },
    )