from __future__ import annotations

from dataclasses import dataclass, field

from app.models.knowledge_graph import GraphNode
from app.services.assistant_engine import (
    AssistantRelationSearchResult,
)


@dataclass(slots=True)
class ScientificCitation:
    """
    Provenance explicite d'une preuve scientifique.

    La citation identifie le document source et,
    lorsqu'elles existent, les informations de
    localisation et de creation de la preuve.
    """

    document: GraphNode
    source_line: int | None = None
    source_text: str | None = None
    created_by: str | None = None


@dataclass(slots=True)
class ScientificFinding:
    """
    Preuve scientifique structuree destinee
    a la construction d'une reponse.
    """

    document: GraphNode
    concept: GraphNode
    relation_type: str
    citation: ScientificCitation | None = None
    confidence: float | None = None
    source_line: int | None = None
    source_text: str | None = None
    created_by: str | None = None

    def __post_init__(self) -> None:
        if (
            self.confidence is not None
            and not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass(slots=True)
class ScientificContradiction:
    """
    Contradiction scientifique explicitement representee
    par une preuve relationnelle.
    """

    document: GraphNode
    concept: GraphNode
    finding: ScientificFinding


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
    studied_concepts: list[GraphNode] = field(
        default_factory=list
    )
    methods: list[GraphNode] = field(
        default_factory=list
    )
    contradictions: list[
        ScientificContradiction
    ] = field(
        default_factory=list
    )

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def studied_concept_count(self) -> int:
        return len(self.studied_concepts)

    @property
    def method_count(self) -> int:
        return len(self.methods)

    @property
    def confidence(self) -> float | None:
        scores = [
            finding.confidence
            for finding in self.findings
            if finding.confidence is not None
        ]

        if not scores:
            return None

        return sum(scores) / len(scores)


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
    contradictions: list[
        ScientificContradiction
    ] = field(
        default_factory=list
    )


    @property
    def confidence(self) -> float | None:
        scores = [
            finding.confidence
            for finding in self.findings
            if finding.confidence is not None
        ]

        if not scores:
            return None

        return sum(scores) / len(scores)


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
                    citation=ScientificCitation(
                        document=evidence.document,
                        source_line=metadata.get(
                            "source_line"
                        ),
                        source_text=metadata.get(
                            "source_text"
                        ),
                        created_by=metadata.get(
                            "created_by"
                        ),
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

        contradictions = [
            ScientificContradiction(
                document=finding.document,
                concept=finding.concept,
                finding=finding,
            )
            for finding in findings
            if finding.relation_type == "contradicts"
        ]

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

            studied_concepts: list[
                GraphNode
            ] = []
            studied_concept_ids: set[str] = set()

            methods: list[GraphNode] = []
            method_ids: set[str] = set()

            for finding in document_findings:
                concept = finding.concept

                if (
                    finding.relation_type == "studies"
                    and concept.node_id
                    not in studied_concept_ids
                ):
                    studied_concept_ids.add(
                        concept.node_id
                    )
                    studied_concepts.append(
                        concept
                    )

                if (
                    finding.relation_type
                    == "uses_method"
                    and concept.node_id
                    not in method_ids
                ):
                    method_ids.add(
                        concept.node_id
                    )
                    methods.append(
                        concept
                    )

            document_contradictions = [
                contradiction
                for contradiction in contradictions
                if (
                    contradiction.document.node_id
                    == document.node_id
                )
            ]

            document_results.append(
                ScientificDocumentResult(
                    document=document,
                    findings=document_findings,
                    studied_concepts=studied_concepts,
                    methods=methods,
                    contradictions=(
                        document_contradictions
                    ),
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
            contradictions=contradictions,
        )
