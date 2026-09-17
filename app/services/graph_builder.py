from __future__ import annotations

from collections.abc import Iterable

from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from app.models.scientific_document import ScientificDocument


class GraphBuilder:
    """
    Construit le Knowledge Graph depuis des documents enrichis.

    V1 :
        document -> noeud document
        entite -> noeud concept canonique
        document -> mentions -> concept

    Les occurrences restent attachees aux aretes mentions.
    """

    def build(
        self,
        documents: Iterable[ScientificDocument],
    ) -> KnowledgeGraph:
        graph = KnowledgeGraph()

        for document in documents:
            if not isinstance(document, ScientificDocument):
                raise TypeError(
                    "Tous les elements doivent etre "
                    "des ScientificDocument."
                )

            document_node_id = (
                f"document:{document.document_id}"
            )

            graph.add_node(
                GraphNode(
                    node_id=document_node_id,
                    node_type="document",
                    label=document.title,
                    metadata={
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "relative_path": document.relative_path,
                    },
                )
            )

            for entity in document.entities:
                concept_node_id = (
                    f"concept:{entity.normalized_key}"
                )

                graph.add_node(
                    GraphNode(
                        node_id=concept_node_id,
                        node_type="concept",
                        label=entity.canonical,
                        metadata={
                            "category": entity.category,
                            "taxonomy_id": entity.taxonomy_id,
                        },
                    )
                )

                graph.add_edge(
                    GraphEdge(
                        source_id=document_node_id,
                        target_id=concept_node_id,
                        relation_type="mentions",
                        occurrences=[entity],
                    )
                )

        return graph
