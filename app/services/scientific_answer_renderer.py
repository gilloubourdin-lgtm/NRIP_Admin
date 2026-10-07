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

        multiple_documents = (
            document_count > 1
        )

        for document_result in (
            answer.document_results
        ):
            semantic_text = (
                self._render_document_semantics(
                    document_result
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
                parts.append(
                    f"{studied_labels[0]} "
                    "est \u00e9tudi\u00e9."
                )
            else:
                parts.append(
                    "Concepts \u00e9tudi\u00e9s : "
                    + self._join_labels(
                        studied_labels
                    )
                    + "."
                )

        if method_labels:
            if len(method_labels) == 1:
                parts.append(
                    "M\u00e9thode utilis\u00e9e : "
                    f"{method_labels[0]}."
                )
            else:
                parts.append(
                    "M\u00e9thodes utilis\u00e9es : "
                    + self._join_labels(
                        method_labels
                    )
                    + "."
                )

        return " ".join(parts)

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
