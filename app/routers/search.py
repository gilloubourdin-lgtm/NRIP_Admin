from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import PROJECT_ROOT, get_settings
from app.services.scientific_search_service import (
    ScientificSearchService,
)


router = APIRouter(
    prefix="/search",
    tags=["search"],
)

templates = Jinja2Templates(
    directory=str(PROJECT_ROOT / "app" / "templates")
)


@router.get("/", response_class=HTMLResponse)
def search_page(
    request: Request,
    query: str | None = None,
):
    cleaned_query = (
        query.strip()
        if query is not None
        else ""
    )

    result = None

    if cleaned_query:
        settings = get_settings()

        result = ScientificSearchService().search(
            root=settings.nrip_root,
            query=cleaned_query,
        )

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "query": cleaned_query,
            "result": result,
        },
    )
