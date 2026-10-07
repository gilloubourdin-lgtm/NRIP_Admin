from __future__ import annotations

from dataclasses import dataclass, field

from app.models.knowledge_graph import GraphNode
from app.services.assistant_engine import (
    AssistantRelationSearchResult,
)


@dataclass(slots=True)
class ScientificFinding:
    """
    Preuve scientifique structuree destinee
    a la construction d'une reponse.
    """

    document: GraphNode
    concept: GraphNode
    relation_type: str
    confidence: float | None = None
    source_line: int | None = None
    source_text: str | None = None
    created_by: str | None = None


@dataclass(slots=True)
class ScientificDocumentResult:
    """
    Resultat scientifique structure pour
    un document individuel.
    """

    document: GraphNode
    findings: list[ScientificFinding] = field(
        default_factory=list
    )


@dataclass(slots=True)
class StructuredScientificAnswer:
    """
    Representation structuree et deterministe
    d'une reponse scientifique.
    """

    found: bool
    document_count: int
    evidence_count: int
    documents: list[GraphNode] = field(
        default_factory=list
    )
    findings: list[ScientificFinding] = field(
        default_factory=list
    )
    document_results: list[
        ScientificDocumentResult
    ] = field(
        default_factory=list
    )


class ScientificAnswerBuilder:
    """
    Transforme un resultat relationnel de
    l'assistant en reponse scientifique structuree.

    Aucun texte libre et aucune inference
    scientifique ne sont produits ici.
    """

    def build(
        self,
        result: AssistantRelationSearchResult,
    ) -> StructuredScientificAnswer:
        if not isinstance(
            result,
            AssistantRelationSearchResult,
        ):
            raise TypeError(
                "result doit etre un "
                "AssistantRelationSearchResult."
            )

        findings: list[ScientificFinding] = []

        for evidence in result.relation_evidence:
            metadata = evidence.relation.metadata

            findings.append(
                ScientificFinding(
                    document=evidence.document,
                    concept=evidence.concept,
                    relation_type=(
                        evidence.relation.relation_type
                    ),
                    confidence=metadata.get(
                        "confidence"
                    ),
                    source_line=metadata.get(
                        "source_line"
                    ),
                    source_text=metadata.get(
                        "source_text"
                    ),
                    created_by=metadata.get(
                        "created_by"
                    ),
                )
            )

        document_results: list[
            ScientificDocumentResult
        ] = []

        for document in result.documents:
            document_findings = [
                finding
                for finding in findings
                if (
                    finding.document.node_id
                    == document.node_id
                )
            ]

            document_results.append(
                ScientificDocumentResult(
                    document=document,
                    findings=document_findings,
                )
            )

        return StructuredScientificAnswer(
            found=result.found,
            document_count=len(result.documents),
            evidence_count=len(
                result.relation_evidence
            ),
            documents=list(result.documents),
            findings=findings,
            document_results=document_results,
        )
