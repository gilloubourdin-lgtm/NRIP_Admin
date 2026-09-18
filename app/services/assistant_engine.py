from __future__ import annotations

from dataclasses import dataclass, field

from app.models.detected_entity import DetectedEntity
from app.models.knowledge_graph import (
    GraphNode,
    KnowledgeGraph,
)
from app.services.graph_query_service import (
    GraphQueryService,
)
from app.services.taxonomy import TaxonomyEngine


@dataclass(slots=True)
class AssistantEvidence:
    """
    Preuve documentaire associee a un concept.

    L'occurrence DetectedEntity reste la source de verite
    pour le texte detecte, les offsets et la provenance.
    """

    document: GraphNode
    concept: GraphNode
    occurrence: DetectedEntity


@dataclass(slots=True)
class AssistantResult:
    """
    Resultat structure d'une recherche scientifique.
    """

    query: str
    found: bool
    concept_id: str | None = None
    concept_label: str | None = None
    ancestors: list[GraphNode] = field(
        default_factory=list
    )
    documents: list[GraphNode] = field(
        default_factory=list
    )
    evidence: list[AssistantEvidence] = field(
        default_factory=list
    )


class AssistantEngine:
    """
    Assistant scientifique deterministe V1.

    Responsabilites :
        terme ou alias
        -> resolution taxonomique
        -> concept canonique
        -> contexte du Knowledge Graph
        -> resultat structure et tracable

    Aucun LLM et aucune inference libre ici.
    """

    def __init__(
        self,
        *,
        graph: KnowledgeGraph,
        taxonomy: TaxonomyEngine | None = None,
    ) -> None:
        if not isinstance(graph, KnowledgeGraph):
            raise TypeError(
                "graph doit etre un KnowledgeGraph."
            )

        self.graph = graph
        self.taxonomy = (
            taxonomy
            if taxonomy is not None
            else TaxonomyEngine()
        )
        self.query_service = GraphQueryService(
            graph
        )

    def lookup(
        self,
        query: str,
    ) -> AssistantResult:
        if not isinstance(query, str):
            raise TypeError(
                "query doit etre une chaine."
            )

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "query ne peut pas etre vide."
            )

        taxonomy_node = self.taxonomy.find(
            cleaned_query
        )

        if taxonomy_node is None:
            return AssistantResult(
                query=cleaned_query,
                found=False,
            )

        concept_id = (
            f"concept:{taxonomy_node.id}"
        )

        concept_node = self.graph.nodes.get(
            concept_id
        )

        if (
            concept_node is None
            or concept_node.node_type != "concept"
        ):
            return AssistantResult(
                query=cleaned_query,
                found=False,
                concept_id=concept_id,
                concept_label=taxonomy_node.name,
            )

        return AssistantResult(
            query=cleaned_query,
            found=True,
            concept_id=concept_id,
            concept_label=concept_node.label,
            ancestors=(
                self.query_service.ancestors_of(
                    concept_id
                )
            ),
            documents=(
                self.query_service.documents_for_concept(
                    concept_id
                )
            ),
            evidence=self._evidence_for_concept(
                concept_node
            ),
        )

    def lookup_family(
        self,
        query: str,
    ) -> AssistantResult:
        if not isinstance(query, str):
            raise TypeError(
                "query doit etre une chaine."
            )

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "query ne peut pas etre vide."
            )

        taxonomy_node = self.taxonomy.find(
            cleaned_query
        )

        if taxonomy_node is None:
            return AssistantResult(
                query=cleaned_query,
                found=False,
            )

        concept_id = (
            f"concept:{taxonomy_node.id}"
        )

        concept_node = self.graph.nodes.get(
            concept_id
        )

        if (
            concept_node is None
            or concept_node.node_type != "concept"
        ):
            return AssistantResult(
                query=cleaned_query,
                found=False,
                concept_id=concept_id,
                concept_label=taxonomy_node.name,
            )

        family_concepts = [
            concept_node,
            *self.query_service.descendants_of(
                concept_id
            ),
        ]

        evidence: list[AssistantEvidence] = []

        for family_concept in family_concepts:
            evidence.extend(
                self._evidence_for_concept(
                    family_concept
                )
            )

        return AssistantResult(
            query=cleaned_query,
            found=True,
            concept_id=concept_id,
            concept_label=concept_node.label,
            ancestors=(
                self.query_service.ancestors_of(
                    concept_id
                )
            ),
            documents=(
                self.query_service
                .documents_for_concept_family(
                    concept_id
                )
            ),
            evidence=evidence,
        )

    def _evidence_for_concept(
        self,
        concept: GraphNode,
    ) -> list[AssistantEvidence]:
        evidence: list[AssistantEvidence] = []

        for edge in self.graph.edges.values():
            if edge.relation_type != "mentions":
                continue

            if edge.target_id != concept.node_id:
                continue

            document = self.graph.nodes.get(
                edge.source_id
            )

            if (
                document is None
                or document.node_type != "document"
            ):
                continue

            for occurrence in edge.occurrences:
                evidence.append(
                    AssistantEvidence(
                        document=document,
                        concept=concept,
                        occurrence=occurrence,
                    )
                )

        return evidence
