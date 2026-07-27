import pytest

from app.models.detected_entity import DetectedEntity


def test_detected_entity_is_normalized():
    entity = DetectedEntity(
        value="  Brett  ",
        canonical="  Brettanomyces  ",
        category=" Organism ",
    )

    assert entity.value == "Brett"
    assert entity.canonical == "Brettanomyces"
    assert entity.category == "organism"


def test_normalized_key_uses_taxonomy_id():
    entity = DetectedEntity(
        value="Brett",
        canonical="Brettanomyces",
        category="organism",
        taxonomy_id=(
            "organism.microorganism.yeast.brettanomyces"
        ),
    )

    assert entity.normalized_key == (
        "organism.microorganism.yeast.brettanomyces"
    )


def test_normalized_key_falls_back_to_category_and_name():
    entity = DetectedEntity(
        value="Brett",
        canonical="Brettanomyces",
        category="organism",
    )

    assert entity.normalized_key == "organism:brettanomyces"


def test_span_length():
    entity = DetectedEntity(
        value="Brett",
        canonical="Brettanomyces",
        category="organism",
        start=10,
        end=15,
    )

    assert entity.length == 5


def test_partial_span_is_rejected():
    with pytest.raises(ValueError):
        DetectedEntity(
            value="Brett",
            canonical="Brettanomyces",
            category="organism",
            start=10,
        )


def test_invalid_span_is_rejected():
    with pytest.raises(ValueError):
        DetectedEntity(
            value="Brett",
            canonical="Brettanomyces",
            category="organism",
            start=10,
            end=5,
        )


def test_entities_overlap():
    first = DetectedEntity(
        value="4-ethylphenol",
        canonical="4-Ethylphenol",
        category="compound",
        start=10,
        end=23,
    )

    second = DetectedEntity(
        value="ethylphenol",
        canonical="Ethylphenol",
        category="compound",
        start=12,
        end=23,
    )

    assert first.overlaps(second) is True