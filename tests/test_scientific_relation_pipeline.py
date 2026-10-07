from app.models.document_relation import DocumentRelation
from app.models.scientific_document import ScientificDocument
from app.services.assistant_engine import AssistantEngine
from app.services.graph_builder import GraphBuilder
from app.services.graph_query_service import GraphQueryService
from app.services.knowledge_engine import KnowledgeEngine
from app.services.scientific_answer_builder import (
    ScientificAnswerBuilder,
)
from app.services.scientific_answer_renderer import (
    ScientificAnswerRenderer,
)


def test_scientific_relation_pipeline_end_to_end():
    text = (
        "Brettanomyces est analyse par GC-MS."
    )

    document = ScientificDocument(
        document_id="NRIP-RELATION-E2E",
        title="Scientific relation pipeline",
        plain_text=text,
    )

    # 1. Extraction deterministe des concepts
    KnowledgeEngine().enrich(document)

    canonical = {
        entity.canonical
        for entity in document.entities
    }

    assert "Brettanomyces" in canonical
    assert "GC-MS" in canonical

    # 2. Relations scientifiques explicites
    document.add_relation(
        DocumentRelation(
            source_id="NRIP-RELATION-E2E",
            target_id=(
                "organism.microorganism."
                "yeast.brettanomyces"
            ),
            relation_type="studies",
            confidence=0.95,
            source_line=1,
            source_text=text,
            created_by="curator",
        )
    )

    document.add_relation(
        DocumentRelation(
            source_id="NRIP-RELATION-E2E",
            target_id=(
                "analysis.chromatography.gc_ms"
            ),
            relation_type="uses_method",
            confidence=0.98,
            source_line=1,
            source_text=text,
            created_by="curator",
        )
    )

    # 3. Construction du Knowledge Graph
    graph = GraphBuilder().build([document])

    document_node_id = (
        "document:NRIP-RELATION-E2E"
    )
    brett_node_id = (
        "concept:"
        "organism.microorganism."
        "yeast.brettanomyces"
    )
    gcms_node_id = (
        "concept:"
        "analysis.chromatography.gc_ms"
    )

    assert document_node_id in graph.nodes
    assert brett_node_id in graph.nodes
    assert gcms_node_id in graph.nodes

    # Les occurrences lexicales restent distinctes
    # des relations scientifiques.
    assert (
        f"{document_node_id}:mentions:{brett_node_id}"
        in graph.edges
    )
    assert (
        f"{document_node_id}:mentions:{gcms_node_id}"
        in graph.edges
    )
    assert (
        f"{document_node_id}:studies:{brett_node_id}"
        in graph.edges
    )
    assert (
        f"{document_node_id}:uses_method:{gcms_node_id}"
        in graph.edges
    )

    # 4. Interrogation scientifique du graphe
    queries = GraphQueryService(graph)

    studied = queries.concepts_studied_by_document(
        "NRIP-RELATION-E2E"
    )
    methods = queries.methods_for_document(
        "NRIP-RELATION-E2E"
    )

    assert [
        node.node_id
        for node in studied
    ] == [
        brett_node_id,
    ]

    assert [
        node.node_id
        for node in methods
    ] == [
        gcms_node_id,
    ]

    assert [
        node.node_id
        for node in queries.documents_studying_concept(
            "organism.microorganism."
            "yeast.brettanomyces"
        )
    ] == [
        document_node_id,
    ]

    assert [
        node.node_id
        for node in queries.documents_using_method(
            "analysis.chromatography.gc_ms"
        )
    ] == [
        document_node_id,
    ]

    # 5. Assistant : preuve lexicale + relationnelle
    assistant = AssistantEngine(graph=graph)

    brett_result = assistant.lookup(
        "Brettanomyces"
    )
    gcms_result = assistant.lookup(
        "GC-MS"
    )

    assert brett_result.found is True
    assert gcms_result.found is True

    assert len(brett_result.evidence) == 1
    assert len(gcms_result.evidence) == 1

    assert len(
        brett_result.relation_evidence
    ) == 1
    assert len(
        gcms_result.relation_evidence
    ) == 1

    brett_relation = (
        brett_result.relation_evidence[0]
        .relation
    )
    gcms_relation = (
        gcms_result.relation_evidence[0]
        .relation
    )

    assert brett_relation.relation_type == (
        "studies"
    )
    assert gcms_relation.relation_type == (
        "uses_method"
    )

    # 6. Provenance preservee jusqu'a l'assistant
    assert brett_relation.metadata[
        "confidence"
    ] == 0.95
    assert gcms_relation.metadata[
        "confidence"
    ] == 0.98

    assert brett_relation.metadata[
        "source_line"
    ] == 1
    assert gcms_relation.metadata[
        "source_line"
    ] == 1

    assert brett_relation.metadata[
        "source_text"
    ] == text
    assert gcms_relation.metadata[
        "source_text"
    ] == text

    assert brett_relation.metadata[
        "created_by"
    ] == "curator"
    assert gcms_relation.metadata[
        "created_by"
    ] == "curator"

    # La preuve lexicale conserve aussi ses offsets.
    brett_occurrence = (
        brett_result.evidence[0].occurrence
    )
    gcms_occurrence = (
        gcms_result.evidence[0].occurrence
    )

    assert text[
        brett_occurrence.start:
        brett_occurrence.end
    ] == "Brettanomyces"

    assert text[
        gcms_occurrence.start:
        gcms_occurrence.end
    ] == "GC-MS"


def test_multi_relation_pipeline_end_to_end():
    text_complete = (
        "Brettanomyces est analyse par GC-MS."
    )
    text_partial = (
        "Brettanomyces est etudie."
    )

    complete = ScientificDocument(
        document_id="NRIP-MULTI-E2E-001",
        title="Complete multi-relation study",
        plain_text=text_complete,
    )

    partial = ScientificDocument(
        document_id="NRIP-MULTI-E2E-002",
        title="Partial multi-relation study",
        plain_text=text_partial,
    )

    # 1. Extraction deterministe des concepts
    engine = KnowledgeEngine()
    engine.enrich(complete)
    engine.enrich(partial)

    assert "Brettanomyces" in {
        entity.canonical
        for entity in complete.entities
    }

    assert "GC-MS" in {
        entity.canonical
        for entity in complete.entities
    }

    assert "Brettanomyces" in {
        entity.canonical
        for entity in partial.entities
    }

    # 2. Relations scientifiques explicites
    complete.add_relation(
        DocumentRelation(
            source_id="NRIP-MULTI-E2E-001",
            target_id=(
                "organism.microorganism."
                "yeast.brettanomyces"
            ),
            relation_type="studies",
            confidence=0.95,
            source_line=1,
            source_text=text_complete,
            created_by="curator",
        )
    )

    complete.add_relation(
        DocumentRelation(
            source_id="NRIP-MULTI-E2E-001",
            target_id=(
                "analysis.chromatography.gc_ms"
            ),
            relation_type="uses_method",
            confidence=0.98,
            source_line=1,
            source_text=text_complete,
            created_by="curator",
        )
    )

    partial.add_relation(
        DocumentRelation(
            source_id="NRIP-MULTI-E2E-002",
            target_id=(
                "organism.microorganism."
                "yeast.brettanomyces"
            ),
            relation_type="studies",
            confidence=0.90,
            source_line=1,
            source_text=text_partial,
            created_by="curator",
        )
    )

    # 3. Construction du graphe avec hierarchie
    graph = GraphBuilder().build(
        [complete, partial]
    )

    # Les descendants sont bien relies
    # aux familles demandees.
    assert (
        "concept:"
        "organism.microorganism."
        "yeast.brettanomyces"
        ":is_a:"
        "concept:"
        "organism.microorganism.yeast"
        in graph.edges
    )

    assert (
        "concept:"
        "organism.microorganism.yeast"
        ":is_a:"
        "concept:organism.microorganism"
        in graph.edges
    )

    assert (
        "concept:"
        "analysis.chromatography.gc_ms"
        ":is_a:"
        "concept:analysis.chromatography"
        in graph.edges
    )

    assert (
        "concept:analysis.chromatography"
        ":is_a:"
        "concept:analysis"
        in graph.edges
    )

    # 4. Recherche scientifique combinee
    assistant = AssistantEngine(graph=graph)

    result = assistant.search_relations(
        [
            (
                "studies",
                "organism.microorganism",
            ),
            (
                "uses_method",
                "analysis",
            ),
        ],
        include_families=True,
    )

    # AND entre contraintes :
    # le document partiel est exclu.
    assert result.found is True

    assert [
        document.node_id
        for document in result.documents
    ] == [
        "document:NRIP-MULTI-E2E-001",
    ]

    # 5. Les preuves restent les relations reelles
    assert len(result.relation_evidence) == 2

    evidence_by_type = {
        evidence.relation.relation_type: evidence
        for evidence in result.relation_evidence
    }

    studies = evidence_by_type["studies"]
    method = evidence_by_type["uses_method"]

    assert studies.document.node_id == (
        "document:NRIP-MULTI-E2E-001"
    )
    assert method.document.node_id == (
        "document:NRIP-MULTI-E2E-001"
    )

    assert studies.concept.node_id == (
        "concept:"
        "organism.microorganism."
        "yeast.brettanomyces"
    )

    assert method.concept.node_id == (
        "concept:"
        "analysis.chromatography.gc_ms"
    )

    # 6. Provenance conservee de bout en bout
    assert studies.relation.metadata[
        "confidence"
    ] == 0.95
    assert studies.relation.metadata[
        "source_line"
    ] == 1
    assert studies.relation.metadata[
        "source_text"
    ] == text_complete
    assert studies.relation.metadata[
        "created_by"
    ] == "curator"

    assert method.relation.metadata[
        "confidence"
    ] == 0.98
    assert method.relation.metadata[
        "source_line"
    ] == 1
    assert method.relation.metadata[
        "source_text"
    ] == text_complete
    assert method.relation.metadata[
        "created_by"
    ] == "curator"

    # Aucune preuve du document incomplet
    # ne doit survivre a l'intersection.
    assert {
        evidence.document.node_id
        for evidence in result.relation_evidence
    } == {
        "document:NRIP-MULTI-E2E-001",
    }

    # 7. Construction de la reponse scientifique structuree
    structured = ScientificAnswerBuilder().build(
        result
    )

    assert structured.found is True
    assert structured.document_count == 1
    assert structured.evidence_count == 2
    assert len(structured.document_results) == 1

    document_result = structured.document_results[0]

    assert document_result.document.node_id == (
        "document:NRIP-MULTI-E2E-001"
    )

    assert [
        concept.label
        for concept in document_result.studied_concepts
    ] == [
        "Brettanomyces",
    ]

    assert [
        method.label
        for method in document_result.methods
    ] == [
        "GC-MS",
    ]

    # 8. Generation textuelle deterministe
    rendered = ScientificAnswerRenderer().render(
        structured
    )

    assert rendered == (
        "1 document correspond \u00e0 la recherche. "
        "Brettanomyces est \u00e9tudi\u00e9. "
        "M\u00e9thode utilis\u00e9e : GC-MS."
    )
