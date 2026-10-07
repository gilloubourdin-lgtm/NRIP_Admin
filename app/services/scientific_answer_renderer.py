from __future__ import annotations

from app.services.scientific_answer_builder import (
    ScientificDocumentResult,
    StructuredScientificAnswer,
)


class ScientificAnswerRenderer:
    """
    Produit une formulation textuelle deterministe
    a partir d'une reponse scientifique structuree.

    Le renderer ne deduit aucun fait scientifique.
    Il formule uniquement les informations deja
    presentes dans StructuredScientificAnswer.
    """

    def render(
        self,
        answer: StructuredScientificAnswer,
        *,
        include_citations: bool = False,
        include_confidence: bool = False,
    ) -> str:
        if not isinstance(
            answer,
            StructuredScientificAnswer,
        ):
            raise TypeError(
                "answer doit etre un "
                "StructuredScientificAnswer."
            )

        if (
            not answer.found
            or not answer.document_results
        ):
            return (
                "Aucun document ne correspond "
                "\u00e0 la recherche."
            )

        document_count = len(
            answer.document_results
        )

        if document_count == 1:
            introduction = (
                "1 document correspond "
                "\u00e0 la recherche."
            )
        else:
            introduction = (
                f"{document_count} documents "
                "correspondent \u00e0 la recherche."
            )

        parts = [introduction]

        if (
            include_confidence
            and answer.confidence is not None
        ):
            confidence_percent = round(
                answer.confidence * 100
            )
            parts.append(
                f"Confiance : {confidence_percent} %."
            )

        multiple_documents = (
            document_count > 1
        )

        for document_result in (
            answer.document_results
        ):
            semantic_text = (
                self._render_document_semantics(
                    document_result,
                    include_citations=include_citations,
                )
            )

            if not semantic_text:
                continue

            if multiple_documents:
                parts.append(
                    f"{document_result.document.label} "
                    f": {semantic_text}"
                )
            else:
                parts.append(
                    semantic_text
                )

        return " ".join(parts)

    def _render_document_semantics(
        self,
        document_result: ScientificDocumentResult,
        *,
        include_citations: bool = False,
    ) -> str:
        parts: list[str] = []

        studied_labels = [
            concept.label
            for concept
            in document_result.studied_concepts
        ]

        method_labels = [
            method.label
            for method
            in document_result.methods
        ]

        if studied_labels:
            if len(studied_labels) == 1:
                sentence = (
                    f"{studied_labels[0]} "
                    "est \u00e9tudi\u00e9."
                )

                if include_citations:
                    citation_text = (
                        self._citation_for_concept(
                            document_result,
                            relation_type="studies",
                            concept_id=(
                                document_result
                                .studied_concepts[0]
                                .node_id
                            ),
                        )
                    )

                    if citation_text:
                        sentence += (
                            f" {citation_text}"
                        )

                parts.append(sentence)
            else:
                rendered_labels = studied_labels

                if include_citations:
                    rendered_labels = []

                    for concept in (
                        document_result
                        .studied_concepts
                    ):
                        label = concept.label
                        citation_text = (
                            self._citation_for_concept(
                                document_result,
                                relation_type="studies",
                                concept_id=concept.node_id,
                            )
                        )

                        if citation_text:
                            label += (
                                f" {citation_text}"
                            )

                        rendered_labels.append(
                            label
                        )

                parts.append(
                    "Concepts \u00e9tudi\u00e9s : "
                    + self._join_labels(
                        rendered_labels
                    )
                    + "."
                )

        if method_labels:
            if len(method_labels) == 1:
                sentence = (
                    "M\u00e9thode utilis\u00e9e : "
                    f"{method_labels[0]}."
                )

                if include_citations:
                    citation_text = (
                        self._citation_for_concept(
                            document_result,
                            relation_type="uses_method",
                            concept_id=(
                                document_result
                                .methods[0]
                                .node_id
                            ),
                        )
                    )

                    if citation_text:
                        sentence += (
                            f" {citation_text}"
                        )

                parts.append(sentence)
            else:
                rendered_labels = method_labels

                if include_citations:
                    rendered_labels = []

                    for method in (
                        document_result
                        .methods
                    ):
                        label = method.label
                        citation_text = (
                            self._citation_for_concept(
                                document_result,
                                relation_type="uses_method",
                                concept_id=method.node_id,
                            )
                        )

                        if citation_text:
                            label += (
                                f" {citation_text}"
                            )

                        rendered_labels.append(
                            label
                        )

                parts.append(
                    "M\u00e9thodes utilis\u00e9es : "
                    + self._join_labels(
                        rendered_labels
                    )
                    + "."
                )

        return " ".join(parts)

    def _citation_for_concept(
        self,
        document_result: ScientificDocumentResult,
        *,
        relation_type: str,
        concept_id: str,
    ) -> str:
        citations: list[str] = []

        for finding in document_result.findings:
            if (
                finding.relation_type
                != relation_type
                or finding.concept.node_id
                != concept_id
                or finding.citation is None
            ):
                continue

            citation = finding.citation
            label = citation.document.label

            if citation.source_line is not None:
                citations.append(
                    f"[{label}, ligne "
                    f"{citation.source_line}]"
                )
            else:
                citations.append(
                    f"[{label}]"
                )

        return " ".join(citations)

    def _join_labels(
        self,
        labels: list[str],
    ) -> str:
        if not labels:
            return ""

        if len(labels) == 1:
            return labels[0]

        if len(labels) == 2:
            return (
                f"{labels[0]} et {labels[1]}"
            )

        return (
            ", ".join(labels[:-1])
            + f" et {labels[-1]}"
        )
