import pytest

from app.services.entity_extraction.spans import SpanBuilder, TextSpan
from app.services.entity_extraction.tokenizer import EntityTokenizer


def test_text_span_properties():
    span = TextSpan(
        value="GC-MS",
        start=10,
        end=15,
        token_count=1,
    )

    assert span.length == 5


def test_text_span_rejects_invalid_token_count():
    with pytest.raises(ValueError):
        TextSpan(
            value="GC-MS",
            start=0,
            end=5,
            token_count=0,
        )


def test_span_builder_builds_single_tokens():
    text = "Brettanomyces produit"

    tokens = EntityTokenizer().tokenize(text)
    spans = SpanBuilder(max_tokens=1).build(text, tokens)

    assert [span.value for span in spans] == [
        "Brettanomyces",
        "produit",
    ]


def test_span_builder_builds_multi_token_candidates():
    text = "Oenococcus oeni produit"

    tokens = EntityTokenizer().tokenize(text)
    spans = SpanBuilder(max_tokens=2).build(text, tokens)

    values = [span.value for span in spans]

    assert "Oenococcus oeni" in values
    assert "oeni produit" in values


def test_span_builder_preserves_original_text():
    text = "Analyse par GC-MS."

    tokens = EntityTokenizer().tokenize(text)
    spans = SpanBuilder(max_tokens=3).build(text, tokens)

    gc_ms = next(
        span for span in spans
        if span.value == "GC-MS"
    )

    assert gc_ms.start == text.index("GC-MS")
    assert gc_ms.end == text.index("GC-MS") + len("GC-MS")
    assert text[gc_ms.start:gc_ms.end] == "GC-MS"


def test_span_builder_preserves_spaces_between_tokens():
    text = "Oenococcus   oeni"

    tokens = EntityTokenizer().tokenize(text)
    spans = SpanBuilder(max_tokens=2).build(text, tokens)

    assert any(
        span.value == "Oenococcus   oeni"
        for span in spans
    )


def test_span_builder_respects_max_tokens():
    text = "un deux trois quatre"

    tokens = EntityTokenizer().tokenize(text)
    spans = SpanBuilder(max_tokens=2).build(text, tokens)

    assert all(
        span.token_count <= 2
        for span in spans
    )

    assert not any(
        span.value == "un deux trois"
        for span in spans
    )


def test_span_builder_empty_tokens_returns_empty_list():
    assert SpanBuilder().build("", []) == []


def test_span_builder_rejects_invalid_max_tokens():
    with pytest.raises(ValueError):
        SpanBuilder(max_tokens=0)


def test_span_builder_rejects_non_string_text():
    with pytest.raises(TypeError):
        SpanBuilder().build(
            None,  # type: ignore[arg-type]
            [],
        )