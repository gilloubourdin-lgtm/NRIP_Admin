from pathlib import Path

from app.services.scientific_search_service import (
    ScientificSearchService,
)


def test_search_finds_document_with_detected_concept(
    tmp_path: Path,
) -> None:
    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    service = ScientificSearchService()

    result = service.search(
        root=tmp_path,
        query="vin",
    )

    assert result.found is True
    assert len(result.documents) == 1
    assert result.documents[0].label == "Wine study"
    assert len(result.evidence) >= 1


def test_search_returns_no_document_for_unknown_concept(
    tmp_path: Path,
) -> None:
    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    service = ScientificSearchService()

    result = service.search(
        root=tmp_path,
        query="concept-inexistant-xyz",
    )

    assert result.found is False
    assert result.documents == []
    assert result.evidence == []
