import pytest

from app.models.text_token import TextToken


def test_text_token_is_created():
    token = TextToken(
        value="Brettanomyces",
        start=0,
        end=13,
    )

    assert token.value == "Brettanomyces"
    assert token.length == 13


def test_text_token_is_immutable():
    token = TextToken(
        value="GC-MS",
        start=0,
        end=5,
    )

    with pytest.raises(Exception):
        token.value = "HPLC"


def test_empty_token_is_rejected():
    with pytest.raises(ValueError):
        TextToken(
            value="",
            start=0,
            end=1,
        )


def test_invalid_start_is_rejected():
    with pytest.raises(ValueError):
        TextToken(
            value="vin",
            start=-1,
            end=2,
        )


def test_invalid_interval_is_rejected():
    with pytest.raises(ValueError):
        TextToken(
            value="vin",
            start=3,
            end=3,
        )


def test_inconsistent_length_is_rejected():
    with pytest.raises(ValueError):
        TextToken(
            value="vin",
            start=0,
            end=4,
        )