import pytest

from app.models.detected_entity import DetectedEntity
from app.models.scientific_document import ScientificDocument
from app.services.knowledge_engine import KnowledgeEngine


@pytest.fixture
def engine() -> KnowledgeEngine:
    return KnowledgeEngine()


def test_enrich_extracts_entities_from_document(engine):
    document = ScientificDocument(
        title="Brettanomyces study",
        plain_text=(
            "Brettanomyces produit du 4-ethylphenol "
            "analyse par GC-MS."
        ),
    )

    result = engine.enrich(document)

    canonical = {
        entity.canonical
        for entity in result.entities
    }

    assert "Brettanomyces" in canonical
    assert "4-éthylphénol" in canonical
    assert "GC-MS" in canonical


def test_enrich_returns_same_document_instance(engine):
    document = ScientificDocument(
        title="GC-MS study",
        plain_text="Analyse par GC-MS.",
    )

    result = engine.enrich(document)

    assert result is document


def test_enrich_preserves_existing_entities(engine):
    existing = DetectedEntity(
        value="Brettanomyces",
        canonical="Brettanomyces",
        category="microorganism",
        taxonomy_id=(
            "organism.microorganism.yeast.brettanomyces"
        ),
        start=100,
        end=113,
    )

    document = ScientificDocument(
        title="Existing knowledge",
        plain_text="Analyse par GC-MS.",
        entities=[existing],
    )

    engine.enrich(document)

    assert existing in document.entities

    assert any(
        entity.canonical == "GC-MS"
        for entity in document.entities
    )


def test_enrich_preserves_distinct_occurrences(engine):
    document = ScientificDocument(
        title="Repeated organism",
        plain_text=(
            "Brettanomyces est etudie. "
            "Brettanomyces est confirme."
        ),
    )

    engine.enrich(document)

    brett = [
        entity
        for entity in document.entities
        if entity.canonical == "Brettanomyces"
    ]

    assert len(brett) == 2
    assert brett[0].occurrence_key != brett[1].occurrence_key


def test_enrich_is_idempotent(engine):
    document = ScientificDocument(
        title="Idempotent enrichment",
        plain_text="Analyse de Brettanomyces par GC-MS.",
    )

    engine.enrich(document)

    first_keys = [
        entity.occurrence_key
        for entity in document.entities
    ]

    engine.enrich(document)

    second_keys = [
        entity.occurrence_key
        for entity in document.entities
    ]

    assert second_keys == first_keys


def test_enrich_recalculates_confidence(engine):
    document = ScientificDocument(
        title="Confidence study",
        plain_text="Analyse de Brettanomyces.",
    )

    assert document.confidence_score == 0.0

    engine.enrich(document)

    assert document.confidence_score > 0.0
    assert document.confidence_score == (
        document.calculate_confidence()
    )


def test_enrich_accepts_empty_plain_text(engine):
    document = ScientificDocument(
        title="Empty content",
    )

    result = engine.enrich(document)

    assert result is document
    assert result.entities == []
    assert result.confidence_score > 0.0


def test_enrich_rejects_non_scientific_document(engine):
    with pytest.raises(TypeError):
        engine.enrich("not a document")
