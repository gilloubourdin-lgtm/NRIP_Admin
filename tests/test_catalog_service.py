from pathlib import Path

from app.services.catalog_service import (
    build_catalog_summary,
    extract_first_title,
    infer_category,
    scan_nrip_documents,
)


def test_extract_first_title() -> None:
    content = "\nTexte préalable\n# Titre scientifique\nContenu"

    assert extract_first_title(content, "Fallback") == "Titre scientifique"


def test_extract_first_title_uses_fallback() -> None:
    assert extract_first_title("Aucun titre Markdown", "Document") == "Document"


def test_infer_category() -> None:
    path = Path("governance") / "NRIP-001_Charter.md"

    assert infer_category(path) == "governance"


def test_scan_nrip_documents(tmp_path: Path) -> None:
    category = tmp_path / "governance"
    category.mkdir()

    document = category / "NRIP-001_Charter.md"
    document.write_text(
        "# NRIP Charter\n\nUn programme scientifique structuré.",
        encoding="utf-8",
    )

    documents = scan_nrip_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].title == "NRIP Charter"
    assert documents[0].category == "governance"
    assert documents[0].relative_path == (
        "governance/NRIP-001_Charter.md"
    )


def test_build_catalog_summary(tmp_path: Path) -> None:
    (tmp_path / "document.md").write_text(
        "# Document\n\nContenu scientifique.",
        encoding="utf-8",
    )

    documents = scan_nrip_documents(tmp_path)
    summary = build_catalog_summary(documents)

    assert summary["document_count"] == 1
    assert summary["categories"] == {"root": 1}

from app.services.catalog_service import (
    infer_content_status,
    infer_structure_family,
)


def test_infer_content_status_empty() -> None:
    assert infer_content_status(0, 0) == "empty"


def test_infer_content_status_short() -> None:
    assert infer_content_status(50, 8) == "short"


def test_infer_content_status_substantial() -> None:
    assert infer_content_status(500, 80) == "substantial"


def test_infer_structure_family_historical() -> None:
    path = Path("03_literature_review") / "document.md"

    assert infer_structure_family(path) == "historical"


def test_infer_structure_family_current() -> None:
    path = Path("literature_review") / "document.md"

    assert infer_structure_family(path) == "current"


def test_infer_structure_family_root() -> None:
    path = Path("0001_Project_Handbook.md")

    assert infer_structure_family(path) == "root"