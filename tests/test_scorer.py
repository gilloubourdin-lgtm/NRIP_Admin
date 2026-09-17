from app.models.detected_entity import DetectedEntity
from app.services.entity_extraction.scorer import EntityScorer


def make_entity(
    value: str,
    *,
    canonical: str | None = None,
    confidence: float = 1.0,
    match_type: str = "exact",
    start: int | None = None,
    end: int | None = None,
) -> DetectedEntity:
    return DetectedEntity(
        value=value,
        canonical=canonical or value,
        category="test",
        confidence=confidence,
        match_type=match_type,
        start=start,
        end=end,
    )


def test_exact_match_has_higher_priority_than_alias():
    scorer = EntityScorer()

    exact = make_entity(
        "GC-MS",
        confidence=1.0,
        match_type="exact",
    )
    alias = make_entity(
        "GCMS",
        confidence=1.0,
        match_type="alias",
    )

    assert scorer.score(exact) > scorer.score(alias)


def test_higher_confidence_has_priority():
    scorer = EntityScorer()

    high = make_entity(
        "Brettanomyces",
        confidence=1.0,
    )
    low = make_entity(
        "Brett",
        confidence=0.9,
    )

    assert scorer.score(high) > scorer.score(low)


def test_longer_span_breaks_equal_score():
    scorer = EntityScorer()

    short = make_entity(
        "Oenococcus",
        start=0,
        end=10,
    )
    long = make_entity(
        "Oenococcus oeni",
        start=0,
        end=15,
    )

    assert scorer.score(long) > scorer.score(short)


def test_rank_orders_best_candidate_first():
    scorer = EntityScorer()

    alias = make_entity(
        "GCMS",
        confidence=0.95,
        match_type="alias",
    )
    exact = make_entity(
        "GC-MS",
        confidence=1.0,
        match_type="exact",
    )

    ranked = scorer.rank([alias, exact])

    assert ranked == [exact, alias]


def test_resolve_overlaps_keeps_longer_equal_candidate():
    scorer = EntityScorer()

    short = make_entity(
        "Oenococcus",
        start=0,
        end=10,
    )
    long = make_entity(
        "Oenococcus oeni",
        start=0,
        end=15,
    )

    resolved = scorer.resolve_overlaps([short, long])

    assert resolved == [long]


def test_resolve_overlaps_keeps_higher_confidence():
    scorer = EntityScorer()

    high = make_entity(
        "GC-MS",
        confidence=1.0,
        start=10,
        end=15,
    )
    low = make_entity(
        "GC-MS analysis",
        confidence=0.8,
        start=10,
        end=24,
    )

    resolved = scorer.resolve_overlaps([low, high])

    assert resolved == [high]


def test_non_overlapping_entities_are_preserved():
    scorer = EntityScorer()

    first = make_entity(
        "Brettanomyces",
        start=0,
        end=13,
    )
    second = make_entity(
        "GC-MS",
        start=25,
        end=30,
    )

    resolved = scorer.resolve_overlaps([second, first])

    assert resolved == [first, second]


def test_adjacent_entities_do_not_overlap():
    scorer = EntityScorer()

    first = make_entity(
        "ABC",
        start=0,
        end=3,
    )
    second = make_entity(
        "DEF",
        start=3,
        end=6,
    )

    resolved = scorer.resolve_overlaps([first, second])

    assert resolved == [first, second]


def test_empty_list_returns_empty_list():
    scorer = EntityScorer()

    assert scorer.rank([]) == []
    assert scorer.resolve_overlaps([]) == []


def test_unknown_match_type_has_lowest_priority():
    scorer = EntityScorer()

    known = make_entity(
        "known",
        match_type="ontology",
    )
    unknown = make_entity(
        "unknown",
        match_type="custom",
    )

    assert scorer.score(known) > scorer.score(unknown)


def test_containing_specific_entity_wins_when_confidence_is_close():
    scorer = EntityScorer()

    generic = make_entity(
        "chromatographie",
        canonical="Chromatographie",
        confidence=1.0,
        match_type="exact",
        start=38,
        end=53,
    )

    specific = make_entity(
        (
            "chromatographie en phase gazeuse couplée "
            "à la spectrométrie de masse"
        ),
        canonical="GC-MS",
        confidence=0.95,
        match_type="alias",
        start=38,
        end=106,
    )

    resolved = scorer.resolve_overlaps(
        [generic, specific]
    )

    assert resolved == [specific]


def test_low_confidence_long_entity_does_not_replace_exact_entity():
    scorer = EntityScorer()

    exact = make_entity(
        "GC-MS",
        confidence=1.0,
        match_type="exact",
        start=10,
        end=15,
    )

    uncertain = make_entity(
        "GC-MS analyse expérimentale",
        confidence=0.70,
        match_type="ontology",
        start=10,
        end=38,
    )

    resolved = scorer.resolve_overlaps(
        [exact, uncertain]
    )

    assert resolved == [exact]