import pytest

from app.services.entity_extraction.tokenizer import EntityTokenizer


def test_empty_text_returns_empty_list():
    tokenizer = EntityTokenizer()

    assert tokenizer.tokenize("") == []


def test_non_string_text_is_rejected():
    tokenizer = EntityTokenizer()

    with pytest.raises(TypeError):
        tokenizer.tokenize(None)  # type: ignore[arg-type]


def test_tokenizer_extracts_simple_words():
    tokenizer = EntityTokenizer()

    tokens = tokenizer.tokenize(
        "Brettanomyces produit des composés volatils."
    )

    assert [token.value for token in tokens] == [
        "Brettanomyces",
        "produit",
        "des",
        "composés",
        "volatils",
    ]


def test_tokenizer_preserves_hyphenated_compound():
    tokenizer = EntityTokenizer()

    tokens = tokenizer.tokenize(
        "Le 4-ethylphenol est quantifié par GC-MS."
    )

    assert [token.value for token in tokens] == [
        "Le",
        "4-ethylphenol",
        "est",
        "quantifié",
        "par",
        "GC-MS",
    ]


def test_tokenizer_preserves_decimal_and_percentage():
    tokenizer = EntityTokenizer()

    tokens = tokenizer.tokenize(
        "La concentration est de 12,5 mg/L et 14 %."
    )

    assert [token.value for token in tokens] == [
        "La",
        "concentration",
        "est",
        "de",
        "12,5",
        "mg",
        "L",
        "et",
        "14 %",
    ]


def test_token_positions_match_source_text():
    tokenizer = EntityTokenizer()
    text = "Analyse par GC-MS."

    tokens = tokenizer.tokenize(text)

    for token in tokens:
        assert text[token.start:token.end] == token.value


def test_repeated_tokens_have_distinct_positions():
    tokenizer = EntityTokenizer()
    text = "vin rouge et vin blanc"

    tokens = tokenizer.tokenize(text)

    first_vin = tokens[0]
    second_vin = tokens[3]

    assert first_vin.value == "vin"
    assert second_vin.value == "vin"
    assert first_vin.start == 0
    assert second_vin.start == 13