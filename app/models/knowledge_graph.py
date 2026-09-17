from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.detected_entity import DetectedEntity


@dataclass(slots=True)
class GraphNode:
    """
    Noeud du Knowledge Graph NRIP.
    """

    node_id: str
    node_type: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.node_id = self.node_id.strip()
        self.node_type = self.node_type.strip().lower()
        self.label = self.label.strip()

        if not self.node_id:
            raise ValueError(
                "GraphNode.node_id ne peut pas etre vide."
            )

        if not self.node_type:
            raise ValueError(
                "GraphNode.node_type ne peut pas etre vide."
            )

        if not self.label:
            raise ValueError(
                "GraphNode.label ne peut pas etre vide."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "GraphNode.metadata doit etre un dictionnaire."
            )


@dataclass(slots=True)
class GraphEdge:
    """
    Arete du Knowledge Graph NRIP.
    """

    source_id: str
    target_id: str
    relation_type: str
    occurrences: list[DetectedEntity] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source_id = self.source_id.strip()
        self.target_id = self.target_id.strip()
        self.relation_type = self.relation_type.strip().lower()

        if not self.source_id:
            raise ValueError(
                "GraphEdge.source_id ne peut pas etre vide."
            )

        if not self.target_id:
            raise ValueError(
                "GraphEdge.target_id ne peut pas etre vide."
            )

        if not self.relation_type:
            raise ValueError(
                "GraphEdge.relation_type ne peut pas etre vide."
            )

        if self.source_id == self.target_id:
            raise ValueError(
                "Une arete ne peut pas relier un noeud a lui-meme."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "GraphEdge.metadata doit etre un dictionnaire."
            )

    @property
    def edge_key(self) -> str:
        return (
            f"{self.source_id}:"
            f"{self.relation_type}:"
            f"{self.target_id}"
        )

    def add_occurrence(
        self,
        occurrence: DetectedEntity,
    ) -> bool:
        existing_keys = {
            entity.occurrence_key
            for entity in self.occurrences
        }

        if occurrence.occurrence_key in existing_keys:
            return False

        self.occurrences.append(occurrence)
        return True


@dataclass(slots=True)
class KnowledgeGraph:
    """
    Representation en memoire du Knowledge Graph NRIP.
    """

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[str, GraphEdge] = field(default_factory=dict)

    def add_node(
        self,
        node: GraphNode,
    ) -> bool:
        existing = self.nodes.get(node.node_id)

        if existing is not None:
            if (
                existing.node_type != node.node_type
                or existing.label != node.label
            ):
                raise ValueError(
                    "Conflit de noeud pour "
                    f"{node.node_id!r}."
                )

            return False

        self.nodes[node.node_id] = node
        return True

    def add_edge(
        self,
        edge: GraphEdge,
    ) -> bool:
        existing = self.edges.get(edge.edge_key)

        if existing is not None:
            for occurrence in edge.occurrences:
                existing.add_occurrence(occurrence)

            return False

        self.edges[edge.edge_key] = edge
        return True
