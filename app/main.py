from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import PROJECT_ROOT, get_settings
from app.routers.dashboard import router as dashboard_router
from app.routers.documents import router as documents_router
from app.services.catalog_service import (
    build_catalog_summary,
    scan_nrip_documents,
)


settings = get_settings()

STATIC_DIR = Path(PROJECT_ROOT) / "app" / "static"

if not STATIC_DIR.exists():
    raise RuntimeError(
        f"Le dossier statique est introuvable : {STATIC_DIR}"
    )

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

app.include_router(dashboard_router)
app.include_router(documents_router)


@app.get("/api/catalog/summary", tags=["api"])
def catalog_summary() -> dict[str, object]:
    documents = scan_nrip_documents(settings.nrip_root)
    return build_catalog_summary(documents)


@app.get("/api/documents", tags=["api"])
def list_documents() -> list[dict[str, object]]:
    documents = scan_nrip_documents(settings.nrip_root)

    return [
        {
            "relative_path": item.relative_path,
            "filename": item.filename,
            "title": item.title,
            "category": item.category,
            "line_count": item.line_count,
            "word_count": item.word_count,
            "size_bytes": item.size_bytes,
            "modified_at": item.modified_at,
            "has_markdown_title": item.has_markdown_title,
            "content_status": item.content_status,
            "structure_family": item.structure_family,
        }
        for item in documents
    ]