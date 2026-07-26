import json
from pathlib import Path

import pytest

from app.services.ontology import (
    OntologyEngine,
    OntologyError,
)


def test_ontology_loads_default_resources():
    engine = OntologyEngine()

    assert engine.concept_count > 0
    assert engine.variant_count > 0
    assert engine.is_known("Brett") is True
    assert engine.is_known("GCMS") is True


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Brett", "Brettanomyces"),
        ("brett", "Brettanomyces"),
        ("Dekkera", "Brettanomyces"),
        ("GCMS", "GC-MS"),
        ("gc ms", "GC-MS"),
        ("FTIR", "FT-IR"),
        ("Pinot Noir", "Pinot noir"),
        ("4 EP", "4-éthylphénol"),
    ],
)
def test_normalize_term(source, expected):
    engine = OntologyEngine()

    assert engine.normalize_term(source) == expected


def test_normalize_unknown_term_preserves_value():
    engine = OntologyEngine()

    assert (
        engine.normalize_term("Concept encore inconnu")
        == "Concept encore inconnu"
    )


def test_normalize_term_removes_surrounding_spaces():
    engine = OntologyEngine()

    assert engine.normalize_term("  GCMS  ") == "GC-MS"


def test_normalize_text_replaces_known_variants():
    engine = OntologyEngine()

    text = (
        "Le Brett a été recherché par GCMS "
        "dans un vin de Pinot Noir."
    )

    normalized = engine.normalize_text(text)

    assert normalized == (
        "Le Brettanomyces a été recherché par GC-MS "
        "dans un vin de Pinot noir."
    )


def test_normalize_text_does_not_replace_inside_words():
    engine = OntologyEngine()

    text = "Le terme BrettTest ne doit pas être remplacé."

    assert engine.normalize_text(text) == text


def test_expand_term_returns_known_variants():
    engine = OntologyEngine()

    variants = engine.expand_term("Brett")

    assert variants[0] == "Brettanomyces"
    assert "Brett" in variants
    assert "Dekkera" in variants


def test_expand_abbreviation_returns_long_definition():
    engine = OntologyEngine()

    variants = engine.expand_term("GC-MS")

    assert "GC-MS" in variants
    assert (
        "chromatographie en phase gazeuse couplée à la spectrométrie de masse"
        in [v.casefold() for v in variants]
    )


def test_statistics_are_consistent():
    engine = OntologyEngine()

    statistics = engine.statistics()

    assert statistics["concepts"] == engine.concept_count
    assert statistics["variants"] == engine.variant_count
    assert statistics["aliases"] > 0
    assert statistics["abbreviations"] > 0
    assert statistics["synonym_groups"] > 0


def test_reload_detects_invalid_json(tmp_path: Path):
    ontology_root = tmp_path / "ontology"
    ontology_root.mkdir()

    (ontology_root / "aliases.json").write_text(
        "{ invalid json",
        encoding="utf-8",
    )
    (ontology_root / "abbreviations.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (ontology_root / "synonyms.json").write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(OntologyError):
        OntologyEngine(ontology_root)


def test_missing_resource_raises_clear_error(tmp_path: Path):
    with pytest.raises(
        OntologyError,
        match="introuvable",
    ):
        OntologyEngine(tmp_path)