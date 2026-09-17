import pytest

from app.services.entity_extraction.matcher import EntityMatcher
from app.services.ontology import OntologyEngine
from app.services.taxonomy import TaxonomyEngine


@pytest.fixture
def matcher() -> EntityMatcher:
    return EntityMatcher(
        taxonomy=TaxonomyEngine(),
        ontology=OntologyEngine(),
    )


def test_exact_brettanomyces_match(matcher):
    entity = matcher.match("Brettanomyces")

    assert entity is not None
    assert entity.value == "Brettanomyces"
    assert entity.canonical == "Brettanomyces"
    assert entity.category == "microorganism"
    assert entity.taxonomy_id == (
        "organism.microorganism.yeast.brettanomyces"
    )
    assert entity.confidence == 1.0
    assert entity.match_type == "exact"


def test_taxonomy_alias_brett_match(matcher):
    entity = matcher.match("Brett")

    assert entity is not None
    assert entity.canonical == "Brettanomyces"
    assert entity.taxonomy_id == (
        "organism.microorganism.yeast.brettanomyces"
    )
    assert entity.match_type == "alias"
    assert entity.confidence == 0.95


def test_dekkera_resolves_to_brettanomyces(matcher):
    entity = matcher.match("Dekkera")

    assert entity is not None
    assert entity.canonical == "Brettanomyces"
    assert entity.taxonomy_id == (
        "organism.microorganism.yeast.brettanomyces"
    )


def test_exact_gc_ms_match(matcher):
    entity = matcher.match("GC-MS")

    assert entity is not None
    assert entity.canonical == "GC-MS"
    assert entity.category == "analytical_method"
    assert entity.taxonomy_id == "analysis.chromatography.gc_ms"
    assert entity.match_type == "exact"


@pytest.mark.parametrize(
    "value",
    [
        "GCMS",
        "GC MS",
        "GC/MS",
    ],
)
def test_gc_ms_aliases(matcher, value):
    entity = matcher.match(value)

    assert entity is not None
    assert entity.canonical == "GC-MS"
    assert entity.taxonomy_id == "analysis.chromatography.gc_ms"
    assert entity.match_type == "alias"


@pytest.mark.parametrize(
    "value",
    [
        "4-ethylphenol",
        "4 EP",
        "4-EP",
    ],
)
def test_ethylphenol_aliases(matcher, value):
    entity = matcher.match(value)

    assert entity is not None
    assert entity.canonical == "4-éthylphénol"
    assert entity.category == "compound"
    assert entity.taxonomy_id == (
        "compound.aromatic.volatile_phenol.4_ep"
    )
    assert entity.match_type == "alias"


def test_oenococcus_oeni_exact_match(matcher):
    entity = matcher.match("Oenococcus oeni")

    assert entity is not None
    assert entity.canonical == "Oenococcus oeni"
    assert entity.category == "microorganism"
    assert entity.taxonomy_id == (
        "organism.microorganism.bacterium.oenococcus_oeni"
    )
    assert entity.match_type == "exact"


def test_unknown_term_returns_none(matcher):
    assert matcher.match(
        "this_term_does_not_exist_in_nrip"
    ) is None


def test_empty_term_returns_none(matcher):
    assert matcher.match("") is None
    assert matcher.match("   ") is None


def test_non_string_term_is_rejected(matcher):
    with pytest.raises(TypeError):
        matcher.match(None)  # type: ignore[arg-type]


def test_match_preserves_source_span(matcher):
    entity = matcher.match(
        "GC-MS",
        start=12,
        end=17,
        source_line=4,
        source_text="Analyse par GC-MS.",
        source_section="Materials and methods",
    )

    assert entity is not None
    assert entity.start == 12
    assert entity.end == 17
    assert entity.source_line == 4
    assert entity.source_text == "Analyse par GC-MS."
    assert entity.source_section == "Materials and methods"


def test_matcher_identifies_itself_as_extractor(matcher):
    entity = matcher.match("Brettanomyces")

    assert entity is not None
    assert entity.extractor == "entity_matcher"