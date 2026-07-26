import pytest

from app.models.detected_entity import DetectedEntity
from app.models.document_relation import DocumentRelation
from app.models.scientific_document import ScientificDocument


def test_detected_entity_normalizes_values():
    entity = DetectedEntity(
        value=" GCMS ",
        canonical=" GC-MS ",
        category=" Analytical_Method ",
        confidence=0.95,
        source_line=12,
    )

    assert entity.value == "GCMS"
    assert entity.canonical == "GC-MS"
    assert entity.category == "analytical_method"
    assert entity.normalized_key == "analytical_method:gc-ms"


def test_detected_entity_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        DetectedEntity(
            value="Brett",
            canonical="Brettanomyces",
            category="microorganism",
            confidence=1.5,
        )


def test_document_relation_builds_stable_key():
    relation = DocumentRelation(
        source_id="doc-001",
        target_id="Brettanomyces",
        relation_type="mentions",
    )

    assert (
        relation.relation_key
        == "doc-001:mentions:Brettanomyces"
    )
    assert relation.is_known_relation_type is True


def test_document_relation_rejects_self_relation():
    with pytest.raises(ValueError):
        DocumentRelation(
            source_id="doc-001",
            target_id="doc-001",
            relation_type="references",
        )


def test_scientific_document_deduplicates_values():
    document = ScientificDocument(
        title="Étude Brettanomyces",
        authors=["Alice Martin", "alice martin", "Bob Dupont"],
        keywords=["vin", "Vin", "microbiologie"],
    )

    assert document.authors == ["Alice Martin", "Bob Dupont"]
    assert document.keywords == ["vin", "microbiologie"]


def test_scientific_document_adds_and_filters_entities():
    document = ScientificDocument(
        title="Analyse microbiologique",
    )

    brett = DetectedEntity(
        value="Brett",
        canonical="Brettanomyces",
        category="microorganism",
        confidence=0.98,
    )

    gcms = DetectedEntity(
        value="GCMS",
        canonical="GC-MS",
        category="analytical_method",
        confidence=0.95,
    )

    assert document.add_entity(brett) is True
    assert document.add_entity(brett) is False
    assert document.add_entity(gcms) is True

    assert document.entity_count == 2

    microorganisms = document.entities_by_category(
        "microorganism"
    )

    assert microorganisms == [brett]
    assert document.canonical_entities(
        "analytical_method"
    ) == ["GC-MS"]


def test_scientific_document_entity_statistics():
    document = ScientificDocument(
        title="Document scientifique",
        entities=[
            DetectedEntity(
                value="Brett",
                canonical="Brettanomyces",
                category="microorganism",
            ),
            DetectedEntity(
                value="Pinot noir",
                canonical="Pinot noir",
                category="grape_variety",
            ),
            DetectedEntity(
                value="GCMS",
                canonical="GC-MS",
                category="analytical_method",
            ),
        ],
    )

    assert document.entity_statistics() == {
        "analytical_method": 1,
        "grape_variety": 1,
        "microorganism": 1,
    }


def test_scientific_document_calculates_confidence():
    document = ScientificDocument(
        title="Essai œnologique",
        authors=["Alice Martin"],
        year=2025,
        plain_text="Analyse de Brettanomyces par GC-MS.",
        keywords=["microbiologie"],
        entities=[
            DetectedEntity(
                value="Brettanomyces",
                canonical="Brettanomyces",
                category="microorganism",
                confidence=0.9,
            )
        ],
    )

    score = document.calculate_confidence()

    assert 0.0 <= score <= 1.0
    assert score > 0.8