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



from urllib.parse import quote


def encode_document_path(value: str) -> str:
    return quote(value, safe="")


templates.env.filters["document_path_urlencode"] = (
    encode_document_path
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

from pathlib import Path, PureWindowsPath

from fastapi import HTTPException

from app.services.document_parser import (
    DocumentParser,
    DocumentParserError,
)


@router.get("/view", response_class=HTMLResponse)
def document_view(request: Request, path: str):
    root = Path(get_settings().nrip_root).expanduser().resolve()

    if not root.is_dir():
        raise HTTPException(
            status_code=404,
            detail="Corpus directory not found.",
        )

    if not path or "\x00" in path:
        raise HTTPException(
            status_code=400,
            detail="Invalid document path.",
        )

    windows_path = PureWindowsPath(path)

    if (
        Path(path).is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or "\\" in path
    ):
        raise HTTPException(
            status_code=400,
            detail="Absolute or invalid path.",
        )

    relative_path = Path(path)

    if (
        relative_path.suffix.lower() != ".md"
        or ".." in relative_path.parts
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Markdown document path.",
        )

    resolved_path = (root / relative_path).resolve()

    try:
        safe_relative_path = resolved_path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Document outside corpus.",
        ) from exc

    if not resolved_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    try:
        document = DocumentParser().parse_file(
            resolved_path,
            root=root,
        )
    except DocumentParserError as exc:
        raise HTTPException(
            status_code=404,
            detail="Document unavailable.",
        ) from exc

    return templates.TemplateResponse(
        request=request,
        name="documents/view.html",
        context={
            "document": document,
            "relative_path": safe_relative_path.as_posix(),
        },
    )
