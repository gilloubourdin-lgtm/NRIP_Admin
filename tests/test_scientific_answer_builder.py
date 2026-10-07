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


def test_structured_answer_groups_findings_by_document():
    document_a = GraphNode(
        node_id="document:NRIP-V6-A",
        node_type="document",
        label="Study A",
    )

    document_b = GraphNode(
        node_id="document:NRIP-V6-B",
        node_type="document",
        label="Study B",
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

    evidence = [
        AssistantRelationEvidence(
            document=document_a,
            concept=brett,
            relation=GraphEdge(
                source_id=document_a.node_id,
                target_id=brett.node_id,
                relation_type="studies",
            ),
        ),
        AssistantRelationEvidence(
            document=document_a,
            concept=gc_ms,
            relation=GraphEdge(
                source_id=document_a.node_id,
                target_id=gc_ms.node_id,
                relation_type="uses_method",
            ),
        ),
        AssistantRelationEvidence(
            document=document_b,
            concept=brett,
            relation=GraphEdge(
                source_id=document_b.node_id,
                target_id=brett.node_id,
                relation_type="studies",
            ),
        ),
    ]

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[
            document_a,
            document_b,
        ],
        relation_evidence=evidence,
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert len(answer.document_results) == 2

    first = answer.document_results[0]
    second = answer.document_results[1]

    assert first.document is document_a
    assert second.document is document_b

    assert [
        finding.relation_type
        for finding in first.findings
    ] == [
        "studies",
        "uses_method",
    ]

    assert [
        finding.concept.label
        for finding in first.findings
    ] == [
        "Brettanomyces",
        "GC-MS",
    ]

    assert [
        finding.relation_type
        for finding in second.findings
    ] == [
        "studies",
    ]

    assert second.findings[0].concept.label == (
        "Brettanomyces"
    )


def test_structured_answer_empty_has_no_document_results():
    result = AssistantRelationSearchResult(
        constraints=[],
        found=False,
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert answer.document_results == []


def test_structured_answer_keeps_document_without_findings():
    document = GraphNode(
        node_id="document:NRIP-V6-NO-EVIDENCE",
        node_type="document",
        label="Document without evidence",
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    assert answer.document_count == 1
    assert len(answer.document_results) == 1

    document_result = answer.document_results[0]

    assert document_result.document is document
    assert document_result.findings == []


def test_document_results_have_independent_finding_lists():
    document_a = GraphNode(
        node_id="document:NRIP-V6-INDEPENDENT-A",
        node_type="document",
        label="Independent A",
    )

    document_b = GraphNode(
        node_id="document:NRIP-V6-INDEPENDENT-B",
        node_type="document",
        label="Independent B",
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[
            document_a,
            document_b,
        ],
        relation_evidence=[],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    first = answer.document_results[0]
    second = answer.document_results[1]

    assert first.findings == []
    assert second.findings == []
    assert first.findings is not second.findings


def test_document_result_exposes_semantic_summary():
    document = GraphNode(
        node_id="document:NRIP-V6-SEMANTIC",
        node_type="document",
        label="Semantic study",
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

    evidence = [
        AssistantRelationEvidence(
            document=document,
            concept=brett,
            relation=GraphEdge(
                source_id=document.node_id,
                target_id=brett.node_id,
                relation_type="studies",
            ),
        ),
        AssistantRelationEvidence(
            document=document,
            concept=gc_ms,
            relation=GraphEdge(
                source_id=document.node_id,
                target_id=gc_ms.node_id,
                relation_type="uses_method",
            ),
        ),
    ]

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=evidence,
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert document_result.studied_concepts == [
        brett
    ]
    assert document_result.methods == [
        gc_ms
    ]


def test_document_result_semantic_summary_is_empty_without_findings():
    document = GraphNode(
        node_id="document:NRIP-V6-SEMANTIC-EMPTY",
        node_type="document",
        label="Semantic empty study",
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert document_result.studied_concepts == []
    assert document_result.methods == []


def test_document_result_semantic_summary_ignores_other_relations():
    document = GraphNode(
        node_id="document:NRIP-V6-SEMANTIC-OTHER",
        node_type="document",
        label="Other relation study",
    )

    concept = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    evidence = AssistantRelationEvidence(
        document=document,
        concept=concept,
        relation=GraphEdge(
            source_id=document.node_id,
            target_id=concept.node_id,
            relation_type="supports",
        ),
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[evidence],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert document_result.studied_concepts == []
    assert document_result.methods == []

    assert len(document_result.findings) == 1
    assert (
        document_result.findings[0].relation_type
        == "supports"
    )


def test_semantic_summary_deduplicates_concepts_but_keeps_findings():
    document = GraphNode(
        node_id="document:NRIP-V6-DEDUP",
        node_type="document",
        label="Deduplication study",
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

    first_relation = GraphEdge(
        source_id=document.node_id,
        target_id=brett.node_id,
        relation_type="studies",
        metadata={
            "source_line": 10,
        },
    )

    second_relation = GraphEdge(
        source_id=document.node_id,
        target_id=brett.node_id,
        relation_type="studies",
        metadata={
            "source_line": 20,
        },
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[
            AssistantRelationEvidence(
                document=document,
                concept=brett,
                relation=first_relation,
            ),
            AssistantRelationEvidence(
                document=document,
                concept=brett,
                relation=second_relation,
            ),
        ],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert len(document_result.findings) == 2

    assert document_result.studied_concepts == [
        brett
    ]


def test_semantic_summary_deduplicates_methods():
    document = GraphNode(
        node_id="document:NRIP-V6-DEDUP-METHOD",
        node_type="document",
        label="Method deduplication study",
    )

    gc_ms = GraphNode(
        node_id=(
            "concept:"
            "analysis.chromatography.gc_ms"
        ),
        node_type="concept",
        label="GC-MS",
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[
            AssistantRelationEvidence(
                document=document,
                concept=gc_ms,
                relation=GraphEdge(
                    source_id=document.node_id,
                    target_id=gc_ms.node_id,
                    relation_type="uses_method",
                    metadata={
                        "source_line": 5,
                    },
                ),
            ),
            AssistantRelationEvidence(
                document=document,
                concept=gc_ms,
                relation=GraphEdge(
                    source_id=document.node_id,
                    target_id=gc_ms.node_id,
                    relation_type="uses_method",
                    metadata={
                        "source_line": 15,
                    },
                ),
            ),
        ],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert len(document_result.findings) == 2

    assert document_result.methods == [
        gc_ms
    ]


def test_document_result_exposes_deterministic_counts():
    document = GraphNode(
        node_id="document:NRIP-V6-COUNTS",
        node_type="document",
        label="Counted study",
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

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[
            AssistantRelationEvidence(
                document=document,
                concept=brett,
                relation=GraphEdge(
                    source_id=document.node_id,
                    target_id=brett.node_id,
                    relation_type="studies",
                ),
            ),
            AssistantRelationEvidence(
                document=document,
                concept=brett,
                relation=GraphEdge(
                    source_id=document.node_id,
                    target_id=brett.node_id,
                    relation_type="studies",
                ),
            ),
            AssistantRelationEvidence(
                document=document,
                concept=gc_ms,
                relation=GraphEdge(
                    source_id=document.node_id,
                    target_id=gc_ms.node_id,
                    relation_type="uses_method",
                ),
            ),
        ],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert document_result.finding_count == 3
    assert document_result.studied_concept_count == 1
    assert document_result.method_count == 1


def test_document_result_empty_counts_are_zero():
    document = GraphNode(
        node_id="document:NRIP-V6-COUNTS-EMPTY",
        node_type="document",
        label="Empty counted study",
    )

    result = AssistantRelationSearchResult(
        constraints=[],
        found=True,
        documents=[document],
        relation_evidence=[],
    )

    answer = ScientificAnswerBuilder().build(
        result
    )

    document_result = answer.document_results[0]

    assert document_result.finding_count == 0
    assert document_result.studied_concept_count == 0
    assert document_result.method_count == 0
