from __future__ import annotations

import pytest

from app.models.knowledge_graph import GraphNode
from app.services.scientific_answer_builder import (
    ScientificDocumentResult,
    ScientificFinding,
    StructuredScientificAnswer,
)
from app.services.scientific_answer_renderer import (
    ScientificAnswerRenderer,
)


def make_structured_answer():
    document = GraphNode(
        node_id="document:NRIP-V7-001",
        node_type="document",
        label="Brettanomyces GC-MS study",
    )

    brett = GraphNode(
        node_id=(
            "concept:"
            "organism.microorganism."
            "yeast.brettanomyces"
        ),
        node_type="concept",
        label="Brettanomyces",
    )

    gc_ms = GraphNode(
        node_id=(
            "concept:"
            "analysis.chromatography.gc_ms"
        ),
        node_type="concept",
        label="GC-MS",
    )

    document_result = ScientificDocumentResult(
        document=document,
        studied_concepts=[brett],
        methods=[gc_ms],
    )

    return StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=2,
        documents=[document],
        document_results=[document_result],
    )


def test_renderer_builds_deterministic_text():
    answer = make_structured_answer()

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Brettanomyces est étudié. "
        "Méthode utilisée : GC-MS."
    )


def test_renderer_handles_no_result():
    answer = StructuredScientificAnswer(
        found=False,
        document_count=0,
        evidence_count=0,
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "Aucun document ne correspond "
        "à la recherche."
    )


def test_renderer_lists_multiple_concepts_and_methods():
    document = GraphNode(
        node_id="document:NRIP-V7-002",
        node_type="document",
        label="Multiple concepts study",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    wine = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    gc_ms = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    hplc = GraphNode(
        node_id="concept:hplc",
        node_type="concept",
        label="HPLC",
    )

    document_result = ScientificDocumentResult(
        document=document,
        studied_concepts=[
            brett,
            wine,
        ],
        methods=[
            gc_ms,
            hplc,
        ],
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=4,
        documents=[document],
        document_results=[document_result],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert "Brettanomyces" in text
    assert "Vin" in text
    assert "GC-MS" in text
    assert "HPLC" in text


def test_renderer_rejects_invalid_input():
    with pytest.raises(TypeError):
        ScientificAnswerRenderer().render(
            object()
        )


def test_renderer_handles_multiple_documents():
    first_document = GraphNode(
        node_id="document:NRIP-V7-MULTI-1",
        node_type="document",
        label="First study",
    )

    second_document = GraphNode(
        node_id="document:NRIP-V7-MULTI-2",
        node_type="document",
        label="Second study",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    gc_ms = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=2,
        evidence_count=2,
        documents=[
            first_document,
            second_document,
        ],
        document_results=[
            ScientificDocumentResult(
                document=first_document,
                studied_concepts=[brett],
            ),
            ScientificDocumentResult(
                document=second_document,
                methods=[gc_ms],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text.startswith(
        "2 documents correspondent "
        "à la recherche."
    )
    assert "Brettanomyces" in text
    assert "GC-MS" in text


def test_renderer_handles_document_without_semantic_summary():
    document = GraphNode(
        node_id="document:NRIP-V7-EMPTY",
        node_type="document",
        label="Document without summary",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=0,
        documents=[document],
        document_results=[
            ScientificDocumentResult(
                document=document,
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "1 document correspond à la recherche."
    )


def test_renderer_does_not_invent_text_from_other_findings():
    document = GraphNode(
        node_id="document:NRIP-V7-SUPPORTS",
        node_type="document",
        label="Supports relation study",
    )

    wine = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    finding = ScientificFinding(
        document=document,
        concept=wine,
        relation_type="supports",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=1,
        documents=[document],
        findings=[finding],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[finding],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "1 document correspond à la recherche."
    )
    assert "Vin" not in text
    assert "supports" not in text


def test_renderer_attributes_semantics_to_each_document():
    first_document = GraphNode(
        node_id="document:NRIP-V7-ATTR-1",
        node_type="document",
        label="Brett study",
    )

    second_document = GraphNode(
        node_id="document:NRIP-V7-ATTR-2",
        node_type="document",
        label="GC-MS study",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    gc_ms = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=2,
        evidence_count=2,
        documents=[
            first_document,
            second_document,
        ],
        document_results=[
            ScientificDocumentResult(
                document=first_document,
                studied_concepts=[brett],
            ),
            ScientificDocumentResult(
                document=second_document,
                methods=[gc_ms],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "2 documents correspondent à la recherche. "
        "Brett study : Brettanomyces est étudié. "
        "GC-MS study : Méthode utilisée : GC-MS."
    )


def test_renderer_keeps_single_document_contract():
    answer = make_structured_answer()

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Brettanomyces est étudié. "
        "Méthode utilisée : GC-MS."
    )


def test_renderer_skips_empty_document_in_multi_document_answer():
    empty_document = GraphNode(
        node_id="document:NRIP-V7-EMPTY-MULTI",
        node_type="document",
        label="Empty study",
    )

    evidence_document = GraphNode(
        node_id="document:NRIP-V7-EVIDENCE",
        node_type="document",
        label="Brett study",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=2,
        evidence_count=1,
        documents=[
            empty_document,
            evidence_document,
        ],
        document_results=[
            ScientificDocumentResult(
                document=empty_document,
            ),
            ScientificDocumentResult(
                document=evidence_document,
                studied_concepts=[brett],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "2 documents correspondent à la recherche. "
        "Brett study : Brettanomyces est étudié."
    )

    assert "Empty study" not in text


def test_renderer_uses_natural_french_for_single_document():
    answer = make_structured_answer()

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Brettanomyces est étudié. "
        "Méthode utilisée : GC-MS."
    )


def test_renderer_uses_natural_french_enumerations():
    document = GraphNode(
        node_id="document:NRIP-V7-FR",
        node_type="document",
        label="Étude œnologique",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    oenococcus = GraphNode(
        node_id="concept:oenococcus_oeni",
        node_type="concept",
        label="Oenococcus oeni",
    )

    gc_ms = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    hplc = GraphNode(
        node_id="concept:hplc",
        node_type="concept",
        label="HPLC",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=4,
        documents=[document],
        document_results=[
            ScientificDocumentResult(
                document=document,
                studied_concepts=[
                    brett,
                    oenococcus,
                ],
                methods=[
                    gc_ms,
                    hplc,
                ],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Concepts étudiés : Brettanomyces "
        "et Oenococcus oeni. "
        "Méthodes utilisées : GC-MS et HPLC."
    )


def test_renderer_uses_natural_french_list_of_three():
    renderer = ScientificAnswerRenderer()

    assert renderer._join_labels(
        ["A", "B", "C"]
    ) == "A, B et C"


def test_renderer_preserves_structured_semantic_order():
    document = GraphNode(
        node_id="document:NRIP-V7-ORDER",
        node_type="document",
        label="Order study",
    )

    first = GraphNode(
        node_id="concept:first",
        node_type="concept",
        label="Premier",
    )

    second = GraphNode(
        node_id="concept:second",
        node_type="concept",
        label="Deuxième",
    )

    third = GraphNode(
        node_id="concept:third",
        node_type="concept",
        label="Troisième",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=3,
        documents=[document],
        document_results=[
            ScientificDocumentResult(
                document=document,
                studied_concepts=[
                    first,
                    second,
                    third,
                ],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert (
        "Concepts étudiés : "
        "Premier, Deuxième et Troisième."
        in text
    )


def test_renderer_preserves_document_order():
    first_document = GraphNode(
        node_id="document:NRIP-V7-ORDER-1",
        node_type="document",
        label="Premier document",
    )

    second_document = GraphNode(
        node_id="document:NRIP-V7-ORDER-2",
        node_type="document",
        label="Deuxième document",
    )

    first_concept = GraphNode(
        node_id="concept:first-order",
        node_type="concept",
        label="Concept A",
    )

    second_concept = GraphNode(
        node_id="concept:second-order",
        node_type="concept",
        label="Concept B",
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=2,
        evidence_count=2,
        documents=[
            first_document,
            second_document,
        ],
        document_results=[
            ScientificDocumentResult(
                document=first_document,
                studied_concepts=[first_concept],
            ),
            ScientificDocumentResult(
                document=second_document,
                studied_concepts=[second_concept],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert text.index(
        "Premier document"
    ) < text.index(
        "Deuxième document"
    )


def test_renderer_does_not_use_finding_source_text():
    document = GraphNode(
        node_id="document:NRIP-V7-SOURCE-TEXT",
        node_type="document",
        label="Source text study",
    )

    concept = GraphNode(
        node_id="concept:source-text",
        node_type="concept",
        label="Concept contrôlé",
    )

    finding = ScientificFinding(
        document=document,
        concept=concept,
        relation_type="supports",
        source_text=(
            "AFFIRMATION NON AUTORISÉE "
            "QUI NE DOIT PAS ÊTRE GÉNÉRÉE"
        ),
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=1,
        documents=[document],
        findings=[finding],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[finding],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer
    )

    assert "AFFIRMATION NON AUTORISÉE" not in text
    assert "Concept contrôlé" not in text
    assert text == (
        "1 document correspond à la recherche."
    )


def test_renderer_can_render_citation_for_studied_concept():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-RENDER-CITATION",
        node_type="document",
        label="Brettanomyces GC-MS study",
    )

    concept = GraphNode(
        node_id=(
            "concept:"
            "organism.microorganism."
            "yeast.brettanomyces"
        ),
        node_type="concept",
        label="Brettanomyces",
    )

    citation = ScientificCitation(
        document=document,
        source_line=12,
        source_text=(
            "SOURCE TEXT MUST NOT BE RENDERED"
        ),
        created_by="curator",
    )

    finding = ScientificFinding(
        document=document,
        concept=concept,
        relation_type="studies",
        citation=citation,
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=1,
        documents=[document],
        findings=[finding],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[finding],
                studied_concepts=[concept],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer,
        include_citations=True,
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Brettanomyces est étudié. "
        "[Brettanomyces GC-MS study, ligne 12]"
    )

    assert (
        "SOURCE TEXT MUST NOT BE RENDERED"
        not in text
    )


def test_renderer_renders_citation_without_source_line():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-CITATION-NO-LINE",
        node_type="document",
        label="Study without line",
    )

    concept = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    finding = ScientificFinding(
        document=document,
        concept=concept,
        relation_type="studies",
        citation=ScientificCitation(
            document=document,
        ),
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=1,
        documents=[document],
        findings=[finding],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[finding],
                studied_concepts=[concept],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer,
        include_citations=True,
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Vin est étudié. "
        "[Study without line]"
    )


def test_renderer_can_render_citation_for_method():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-METHOD-CITATION",
        node_type="document",
        label="GC-MS method study",
    )

    method = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    finding = ScientificFinding(
        document=document,
        concept=method,
        relation_type="uses_method",
        citation=ScientificCitation(
            document=document,
            source_line=42,
            source_text=(
                "METHOD SOURCE TEXT MUST NOT BE RENDERED"
            ),
        ),
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=1,
        documents=[document],
        findings=[finding],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[finding],
                methods=[method],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer,
        include_citations=True,
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Méthode utilisée : GC-MS. "
        "[GC-MS method study, ligne 42]"
    )

    assert (
        "METHOD SOURCE TEXT MUST NOT BE RENDERED"
        not in text
    )


def test_renderer_preserves_multiple_citations_for_same_fact():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-MULTI-CITATION",
        node_type="document",
        label="Brett study",
    )

    concept = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    first_finding = ScientificFinding(
        document=document,
        concept=concept,
        relation_type="studies",
        citation=ScientificCitation(
            document=document,
            source_line=10,
        ),
    )

    second_finding = ScientificFinding(
        document=document,
        concept=concept,
        relation_type="studies",
        citation=ScientificCitation(
            document=document,
            source_line=20,
        ),
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=2,
        documents=[document],
        findings=[
            first_finding,
            second_finding,
        ],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[
                    first_finding,
                    second_finding,
                ],
                studied_concepts=[concept],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer,
        include_citations=True,
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Brettanomyces est étudié. "
        "[Brett study, ligne 10] "
        "[Brett study, ligne 20]"
    )

    assert text.index(
        "[Brett study, ligne 10]"
    ) < text.index(
        "[Brett study, ligne 20]"
    )


def test_renderer_attributes_citations_to_multiple_concepts():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-MULTI-CONCEPT-CITATION",
        node_type="document",
        label="Multi concept study",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    wine = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    brett_finding = ScientificFinding(
        document=document,
        concept=brett,
        relation_type="studies",
        citation=ScientificCitation(
            document=document,
            source_line=10,
        ),
    )

    wine_finding = ScientificFinding(
        document=document,
        concept=wine,
        relation_type="studies",
        citation=ScientificCitation(
            document=document,
            source_line=20,
        ),
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=2,
        documents=[document],
        findings=[
            brett_finding,
            wine_finding,
        ],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[
                    brett_finding,
                    wine_finding,
                ],
                studied_concepts=[
                    brett,
                    wine,
                ],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer,
        include_citations=True,
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Concepts étudiés : "
        "Brettanomyces "
        "[Multi concept study, ligne 10] "
        "et Vin "
        "[Multi concept study, ligne 20]."
    )


def test_renderer_attributes_citations_to_multiple_methods():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-MULTI-METHOD-CITATION",
        node_type="document",
        label="Multi method study",
    )

    gc_ms = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    hplc = GraphNode(
        node_id="concept:hplc",
        node_type="concept",
        label="HPLC",
    )

    gc_ms_finding = ScientificFinding(
        document=document,
        concept=gc_ms,
        relation_type="uses_method",
        citation=ScientificCitation(
            document=document,
            source_line=30,
        ),
    )

    hplc_finding = ScientificFinding(
        document=document,
        concept=hplc,
        relation_type="uses_method",
        citation=ScientificCitation(
            document=document,
            source_line=40,
        ),
    )

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=2,
        documents=[document],
        findings=[
            gc_ms_finding,
            hplc_finding,
        ],
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=[
                    gc_ms_finding,
                    hplc_finding,
                ],
                methods=[
                    gc_ms,
                    hplc,
                ],
            ),
        ],
    )

    text = ScientificAnswerRenderer().render(
        answer,
        include_citations=True,
    )

    assert text == (
        "1 document correspond à la recherche. "
        "Méthodes utilisées : "
        "GC-MS "
        "[Multi method study, ligne 30] "
        "et HPLC "
        "[Multi method study, ligne 40]."
    )


def test_renderer_keeps_v7_output_when_citations_are_disabled():
    from app.services.scientific_answer_builder import (
        ScientificCitation,
    )

    document = GraphNode(
        node_id="document:NRIP-V8-V7-COMPAT",
        node_type="document",
        label="Compatibility study",
    )

    brett = GraphNode(
        node_id="concept:brettanomyces",
        node_type="concept",
        label="Brettanomyces",
    )

    wine = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    gc_ms = GraphNode(
        node_id="concept:gc_ms",
        node_type="concept",
        label="GC-MS",
    )

    hplc = GraphNode(
        node_id="concept:hplc",
        node_type="concept",
        label="HPLC",
    )

    findings = [
        ScientificFinding(
            document=document,
            concept=brett,
            relation_type="studies",
            citation=ScientificCitation(
                document=document,
                source_line=10,
            ),
        ),
        ScientificFinding(
            document=document,
            concept=wine,
            relation_type="studies",
            citation=ScientificCitation(
                document=document,
                source_line=20,
            ),
        ),
        ScientificFinding(
            document=document,
            concept=gc_ms,
            relation_type="uses_method",
            citation=ScientificCitation(
                document=document,
                source_line=30,
            ),
        ),
        ScientificFinding(
            document=document,
            concept=hplc,
            relation_type="uses_method",
            citation=ScientificCitation(
                document=document,
                source_line=40,
            ),
        ),
    ]

    answer = StructuredScientificAnswer(
        found=True,
        document_count=1,
        evidence_count=4,
        documents=[document],
        findings=findings,
        document_results=[
            ScientificDocumentResult(
                document=document,
                findings=findings,
                studied_concepts=[
                    brett,
                    wine,
                ],
                methods=[
                    gc_ms,
                    hplc,
                ],
            ),
        ],
    )

    renderer = ScientificAnswerRenderer()

    default_text = renderer.render(
        answer,
    )

    explicit_text = renderer.render(
        answer,
        include_citations=False,
    )

    expected = (
        "1 document correspond à la recherche. "
        "Concepts étudiés : Brettanomyces et Vin. "
        "Méthodes utilisées : GC-MS et HPLC."
    )

    assert default_text == expected
    assert explicit_text == expected
    assert "[" not in default_text
    assert "[" not in explicit_text
