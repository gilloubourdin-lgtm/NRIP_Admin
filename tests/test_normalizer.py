import pytest

from app.services.entity_extraction.normalizer import EntityNormalizer


def test_normalizer_lowercases_text():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("Brettanomyces") == "brettanomyces"


def test_normalizer_strips_outer_whitespace():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("  GC-MS  ") == "gcms"


def test_normalizer_harmonizes_gc_ms_variants():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("GC-MS") == "gcms"
    assert normalizer.normalize("GC/MS") == "gcms"
    assert normalizer.normalize("GC MS") == "gcms"
    assert normalizer.normalize("GC_MS") == "gcms"


def test_normalizer_harmonizes_hyphenated_compound():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("4-ethylphenol") == "4ethylphenol"
    assert normalizer.normalize("4 ethylphenol") == "4ethylphenol"


def test_normalizer_harmonizes_unicode_dashes():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("GC–MS") == "gcms"
    assert normalizer.normalize("GC—MS") == "gcms"


def test_normalizer_uses_casefold():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("STRAẞE") == "strasse"


def test_normalizer_preserves_accented_characters():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("Éthanol") == "éthanol"


def test_normalizer_preserves_greek_characters():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("β-glucosidase") == "βglucosidase"


def test_empty_string_returns_empty_string():
    normalizer = EntityNormalizer()

    assert normalizer.normalize("") == ""
    assert normalizer.normalize("   ") == ""


def test_non_string_value_is_rejected():
    normalizer = EntityNormalizer()

    with pytest.raises(TypeError):
        normalizer.normalize(None)  # type: ignore[arg-type]


def test_normalize_phrase_preserves_word_boundaries():
    normalizer = EntityNormalizer()

    assert (
        normalizer.normalize_phrase("  Oenococcus   oeni  ")
        == "oenococcus oeni"
    )


def test_normalize_phrase_preserves_hyphen():
    normalizer = EntityNormalizer()

    assert normalizer.normalize_phrase("GC-MS") == "gc-ms"