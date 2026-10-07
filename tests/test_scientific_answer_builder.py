from __future__ import annotations

import pytest

from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
)
from app.services.assistant_engine import (
    AssistantRelationEvidence,
    AssistantRelationSearchResult,
)
from app.services.scientific_answer_builder import (
    ScientificAnswerBuilder,
)


def make_relation_result():
    document = GraphNode(
        node_id="document:NRIP-V6-001",
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

    relation = GraphEdge(
        source_id=document.node_id,
        target_id=concept.node_id,
        relation_type="studies",
        metadata={
            "confidence": 0.95,
            "source_line": 12,
            "source_text": (
                "Brettanomyces was analysed."
            ),
            "created_by": "curator",
        },
    )

    evidence = AssistantRelationEvidence(
        document=document,
        concept=concept,
        relation=relation,
    )

    return AssistantRelationSearchResult(
        constraints=[
            (
                "studies",
                "organism.microorganism",
            ),
        ],
        found=True,
        documents=[document],
        relation_evidence=[evidence],
    )


def test_structured_answer_builds_finding():
    result = make_relation_result()

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert answer.found is True
    assert answer.document_count == 1
    assert answer.evidence_count == 1
    assert answer.documents == result.documents

    assert len(answer.findings) == 1

    finding = answer.findings[0]

    assert finding.document.node_id == (
        "document:NRIP-V6-001"
    )
    assert finding.concept.label == (
        "Brettanomyces"
    )
    assert finding.relation_type == "studies"


def test_structured_answer_preserves_provenance():
    result = make_relation_result()

    answer = ScientificAnswerBuilder().build(
        result
    )

    finding = answer.findings[0]

    assert finding.confidence == 0.95
    assert finding.source_line == 12
    assert finding.source_text == (
        "Brettanomyces was analysed."
    )
    assert finding.created_by == "curator"


def test_structured_answer_handles_empty_result():
    result = AssistantRelationSearchResult(
        constraints=[],
        found=False,
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert answer.found is False
    assert answer.document_count == 0
    assert answer.evidence_count == 0
    assert answer.documents == []
    assert answer.findings == []


def test_structured_answer_rejects_invalid_input():
    with pytest.raises(TypeError):
        ScientificAnswerBuilder().build(
            object()
        )


def test_structured_answer_preserves_multiple_findings():
    result = make_relation_result()

    document = result.documents[0]

    method = GraphNode(
        node_id=(
            "concept:"
            "analysis.chromatography.gc_ms"
        ),
        node_type="concept",
        label="GC-MS",
    )

    relation = GraphEdge(
        source_id=document.node_id,
        target_id=method.node_id,
        relation_type="uses_method",
        metadata={
            "confidence": 0.98,
            "source_line": 12,
            "source_text": (
                "Brettanomyces was analysed "
                "by GC-MS."
            ),
            "created_by": "curator",
        },
    )

    result.relation_evidence.append(
        AssistantRelationEvidence(
            document=document,
            concept=method,
            relation=relation,
        )
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert answer.document_count == 1
    assert answer.evidence_count == 2
    assert len(answer.findings) == 2

    assert [
        finding.relation_type
        for finding in answer.findings
    ] == [
        "studies",
        "uses_method",
    ]

    assert [
        finding.concept.label
        for finding in answer.findings
    ] == [
        "Brettanomyces",
        "GC-MS",
    ]


def test_structured_answer_handles_missing_metadata():
    document = GraphNode(
        node_id="document:NRIP-V6-EMPTY-META",
        node_type="document",
        label="Study without provenance",
    )

    concept = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    relation = GraphEdge(
        source_id=document.node_id,
        target_id=concept.node_id,
        relation_type="studies",
    )

    result = AssistantRelationSearchResult(
        constraints=[
            ("studies", "wine"),
        ],
        found=True,
        documents=[document],
        relation_evidence=[
            AssistantRelationEvidence(
                document=document,
                concept=concept,
                relation=relation,
            )
        ],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    finding = answer.findings[0]

    assert finding.confidence is None
    assert finding.source_line is None
    assert finding.source_text is None
    assert finding.created_by is None


def test_structured_answer_copies_document_list():
    result = make_relation_result()

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert answer.documents == result.documents
    assert answer.documents is not result.documents
