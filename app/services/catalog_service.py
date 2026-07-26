from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from app.models.document import DocumentRecord


MARKDOWN_TITLE_PATTERN = re.compile(r"^\s*#\s+(.+?)\s*$")


class CatalogError(RuntimeError):
    """Erreur liée à la lecture du corpus NRIP."""


def extract_first_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        match = MARKDOWN_TITLE_PATTERN.match(line)
        if match:
            return match.group(1).strip()

    return fallback


def infer_category(relative_path: Path) -> str:
    if len(relative_path.parts) > 1:
        return relative_path.parts[0]

    return "root"


def scan_nrip_documents(nrip_root: Path) -> list[DocumentRecord]:
    root = nrip_root.expanduser().resolve()

    if not root.exists():
        raise CatalogError(f"Le dossier NRIP est introuvable : {root}")

    if not root.is_dir():
        raise CatalogError(f"Le chemin NRIP n'est pas un dossier : {root}")

    documents: list[DocumentRecord] = []

    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise CatalogError(
                f"Impossible de lire le document : {path}"
            ) from exc

        relative_path = path.relative_to(root)
        stat = path.stat()

        lines = content.splitlines()
        line_count = len(lines)
        word_count = len(content.split())

        documents.append(
            DocumentRecord(
                relative_path=relative_path.as_posix(),
                filename=path.name,
                title=extract_first_title(content, path.stem),
                category=infer_category(relative_path),
                line_count=line_count,
                word_count=word_count,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat(timespec="seconds"),
                has_markdown_title=has_markdown_title(content),
                content_status=infer_content_status(
                    word_count=word_count,
                    line_count=line_count,
                ),
                structure_family=infer_structure_family(relative_path),
            )
        )

    return documents


def build_catalog_summary(
    documents: list[DocumentRecord],
) -> dict[str, object]:
    categories: dict[str, int] = {}
    content_statuses: dict[str, int] = {}
    structure_families: dict[str, int] = {}

    documents_without_title = 0

    for document in documents:
        categories[document.category] = (
            categories.get(document.category, 0) + 1
        )

        content_statuses[document.content_status] = (
            content_statuses.get(document.content_status, 0) + 1
        )

        structure_families[document.structure_family] = (
            structure_families.get(document.structure_family, 0) + 1
        )

        if not document.has_markdown_title:
            documents_without_title += 1

    return {
        "document_count": len(documents),
        "line_count": sum(item.line_count for item in documents),
        "word_count": sum(item.word_count for item in documents),
        "size_bytes": sum(item.size_bytes for item in documents),
        "categories": dict(sorted(categories.items())),
        "content_statuses": dict(sorted(content_statuses.items())),
        "structure_families": dict(sorted(structure_families.items())),
        "documents_without_title": documents_without_title,
    }

def has_markdown_title(content: str) -> bool:
    return any(
        MARKDOWN_TITLE_PATTERN.match(line)
        for line in content.splitlines()
    )


def infer_content_status(
    word_count: int,
    line_count: int,
) -> str:
    if word_count == 0:
        return "empty"

    if word_count < 100 or line_count < 10:
        return "short"

    return "substantial"


def infer_structure_family(relative_path: Path) -> str:
    if not relative_path.parts:
        return "unknown"

    if len(relative_path.parts) == 1:
        return "root"

    first_part = relative_path.parts[0]

    if first_part[:2].isdigit() and "_" in first_part:
        return "historical"

    return "current"