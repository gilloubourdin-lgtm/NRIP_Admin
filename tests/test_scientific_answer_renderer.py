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
        "1 document correspond a la recherche. "
        "Brettanomyces est etudie. "
        "Methode utilisee : GC-MS."
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
        "a la recherche."
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
        "a la recherche."
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
        "1 document correspond a la recherche."
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
        "1 document correspond a la recherche."
    )
    assert "Vin" not in text
    assert "supports" not in text
