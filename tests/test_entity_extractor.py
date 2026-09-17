import pytest

from app.services.entity_extraction.extractor import EntityExtractor


@pytest.fixture
def extractor() -> EntityExtractor:
    return EntityExtractor()


def test_extract_brettanomyces(extractor):
    entities = extractor.extract(
        "Brettanomyces est une levure d'altération."
    )

    assert any(
        entity.canonical == "Brettanomyces"
        for entity in entities
    )


def test_extract_gc_ms(extractor):
    text = "L'analyse est réalisée par GC-MS."

    entities = extractor.extract(text)

    gc_ms = next(
        entity
        for entity in entities
        if entity.canonical == "GC-MS"
    )

    assert gc_ms.category == "analytical_method"
    assert gc_ms.taxonomy_id == "analysis.chromatography.gc_ms"
    assert gc_ms.value == "GC-MS"
    assert text[gc_ms.start:gc_ms.end] == "GC-MS"


def test_extract_multi_token_organism(extractor):
    text = "Oenococcus oeni intervient pendant la fermentation."

    entities = extractor.extract(text)

    organism = next(
        entity
        for entity in entities
        if entity.canonical == "Oenococcus oeni"
    )

    assert organism.category == "microorganism"
    assert organism.taxonomy_id == (
        "organism.microorganism.bacterium.oenococcus_oeni"
    )
    assert organism.value == "Oenococcus oeni"


def test_extract_compound_alias(extractor):
    text = "La concentration de 4-EP a été mesurée."

    entities = extractor.extract(text)

    compound = next(
        entity
        for entity in entities
        if entity.canonical == "4-éthylphénol"
    )

    assert compound.category == "compound"
    assert compound.taxonomy_id == (
        "compound.aromatic.volatile_phenol.4_ep"
    )
    assert compound.value == "4-EP"


def test_extract_multiple_entities(extractor):
    text = (
        "Brettanomyces produit du 4-éthylphénol "
        "analysé par GC-MS."
    )

    entities = extractor.extract(text)

    canonical = {
        entity.canonical
        for entity in entities
    }

    assert "Brettanomyces" in canonical
    assert "4-éthylphénol" in canonical
    assert "GC-MS" in canonical


def test_entities_are_ordered_by_text_position(extractor):
    text = "Brettanomyces est analysé par GC-MS."

    entities = extractor.extract(text)

    positions = [
        entity.start
        for entity in entities
    ]

    assert positions == sorted(positions)


def test_extract_preserves_source_text(extractor):
    text = "Analyse de Brettanomyces par GC-MS."

    entities = extractor.extract(
        text,
        source_line=12,
        source_section="Results",
    )

    assert entities

    for entity in entities:
        assert entity.source_text == text
        assert entity.source_line == 12
        assert entity.source_section == "Results"


def test_extract_preserves_exact_spans(extractor):
    text = "Étude de Oenococcus oeni et GC-MS."

    entities = extractor.extract(text)

    for entity in entities:
        assert entity.start is not None
        assert entity.end is not None
        assert text[entity.start:entity.end] == entity.value


def test_empty_text_returns_empty_list(extractor):
    assert extractor.extract("") == []
    assert extractor.extract("   ") == []


def test_unknown_text_returns_empty_list(extractor):
    entities = extractor.extract(
        "Cette phrase ne contient aucun concept répertorié."
    )

    assert entities == []


def test_non_string_text_is_rejected(extractor):
    with pytest.raises(TypeError):
        extractor.extract(None)  # type: ignore[arg-type]


def test_extract_long_gc_ms_alias(extractor):
    text = (
        "Les échantillons ont été analysés par "
        "chromatographie en phase gazeuse couplée "
        "à la spectrométrie de masse."
    )

    entities = extractor.extract(text)

    gc_ms = next(
        entity
        for entity in entities
        if entity.canonical == "GC-MS"
    )

    assert gc_ms.value == (
        "chromatographie en phase gazeuse couplée "
        "à la spectrométrie de masse"
    )
    assert gc_ms.category == "analytical_method"
    assert gc_ms.taxonomy_id == "analysis.chromatography.gc_ms"
    assert gc_ms.match_type == "alias"
    assert gc_ms.confidence == 0.95
    assert text[gc_ms.start:gc_ms.end] == gc_ms.value

    assert not any(
        entity.canonical == "Chromatographie"
        for entity in entities
    )