from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ONTOLOGY_ROOT = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "ontology"
)


class OntologyError(RuntimeError):
    """Erreur liée au chargement ou à l’utilisation de l’ontologie."""


class OntologyEngine:
    """
    Normalise les variantes linguistiques et scientifiques du corpus.

    Responsabilités :
    - charger les alias, abréviations et synonymes ;
    - convertir une variante vers une forme canonique ;
    - normaliser un texte complet ;
    - fournir les variantes connues d’un concept.

    Ce moteur ne classe pas les concepts. La classification appartient
    au futur TaxonomyEngine.
    """

    def __init__(
        self,
        ontology_root: Path | str | None = None,
    ) -> None:
        self.ontology_root = Path(
            ontology_root or DEFAULT_ONTOLOGY_ROOT
        )

        self.aliases: dict[str, str] = {}
        self.abbreviations: dict[str, str] = {}
        self.synonyms: dict[str, list[str]] = {}

        self._alias_to_canonical: dict[str, str] = {}
        self._canonical_to_variants: dict[str, list[str]] = {}
        self._normalization_pattern: re.Pattern[str] | None = None

        self.reload()

    def reload(self) -> None:
        """
        Recharge toutes les ressources d’ontologie depuis le disque.
        """
        self.aliases = self._load_mapping("aliases.json")
        self.abbreviations = self._load_mapping(
            "abbreviations.json"
        )
        self.synonyms = self._load_synonyms("synonyms.json")

        self._build_indexes()
        self._normalization_pattern = (
            self._build_normalization_pattern()
        )

    def _load_json(self, filename: str) -> dict[str, Any]:
        path = self.ontology_root / filename

        if not path.exists():
            raise OntologyError(
                f"Ressource d’ontologie introuvable : {path}"
            )

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise OntologyError(
                f"JSON invalide dans {path} : {exc}"
            ) from exc
        except OSError as exc:
            raise OntologyError(
                f"Impossible de lire {path} : {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise OntologyError(
                f"La racine de {path} doit être un objet JSON."
            )

        return data

    def _load_mapping(self, filename: str) -> dict[str, str]:
        raw = self._load_json(filename)
        result: dict[str, str] = {}

        for key, value in raw.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise OntologyError(
                    f"{filename} doit contenir uniquement "
                    "des associations chaîne → chaîne."
                )

            alias = key.strip()
            canonical = value.strip()

            if alias and canonical:
                result[alias] = canonical

        return result

    def _load_synonyms(
        self,
        filename: str,
    ) -> dict[str, list[str]]:
        raw = self._load_json(filename)
        result: dict[str, list[str]] = {}

        for canonical, variants in raw.items():
            if not isinstance(canonical, str):
                raise OntologyError(
                    f"Clé canonique invalide dans {filename}."
                )

            if not isinstance(variants, list):
                raise OntologyError(
                    f"Les synonymes de {canonical!r} "
                    "doivent être une liste."
                )

            cleaned_variants: list[str] = []

            for variant in variants:
                if not isinstance(variant, str):
                    raise OntologyError(
                        f"Synonyme non textuel pour {canonical!r}."
                    )

                cleaned = variant.strip()

                if cleaned:
                    cleaned_variants.append(cleaned)

            canonical_clean = canonical.strip()

            if canonical_clean:
                result[canonical_clean] = self._deduplicate(
                    [canonical_clean, *cleaned_variants]
                )

        return result

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = value.strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(cleaned)

        return result

    def _register_variant(
        self,
        variant: str,
        canonical: str,
    ) -> None:
        variant_clean = variant.strip()
        canonical_clean = canonical.strip()

        if not variant_clean or not canonical_clean:
            return

        self._alias_to_canonical[
            variant_clean.casefold()
        ] = canonical_clean

        current = self._canonical_to_variants.setdefault(
            canonical_clean,
            [],
        )

        current.append(variant_clean)
        self._canonical_to_variants[canonical_clean] = (
            self._deduplicate(current)
        )

    def _build_indexes(self) -> None:
        self._alias_to_canonical = {}
        self._canonical_to_variants = {}

        for alias, canonical in self.aliases.items():
            self._register_variant(alias, canonical)
            self._register_variant(canonical, canonical)

        for canonical, variants in self.synonyms.items():
            self._register_variant(canonical, canonical)

            for variant in variants:
                self._register_variant(variant, canonical)

        # Les abréviations restent canoniques. Leur forme longue est
        # ajoutée comme variante permettant de les retrouver.
        for abbreviation, definition in self.abbreviations.items():
            self._register_variant(
                abbreviation,
                abbreviation,
            )
            self._register_variant(
                definition,
                abbreviation,
            )

    def _build_normalization_pattern(
        self,
    ) -> re.Pattern[str] | None:
        variants = [
            variant
            for variant in self._alias_to_canonical
            if variant
        ]

        if not variants:
            return None

        # Les expressions longues doivent être évaluées avant les
        # expressions courtes afin d’éviter les remplacements partiels.
        variants.sort(key=len, reverse=True)

        escaped = [re.escape(value) for value in variants]

        return re.compile(
            r"(?<!\w)(" + "|".join(escaped) + r")(?!\w)",
            flags=re.IGNORECASE,
        )

    @property
    def concept_count(self) -> int:
        return len(self._canonical_to_variants)

    @property
    def variant_count(self) -> int:
        return len(self._alias_to_canonical)

    def find_alias(self, value: str) -> str | None:
        """
        Retourne la forme canonique connue d’une variante.
        """
        cleaned = value.strip()

        if not cleaned:
            return None

        return self._alias_to_canonical.get(
            cleaned.casefold()
        )

    def normalize_term(self, value: str) -> str:
        """
        Normalise un terme isolé.

        Une valeur inconnue est retournée nettoyée mais inchangée.
        """
        cleaned = value.strip()

        if not cleaned:
            return ""

        return self.find_alias(cleaned) or cleaned

    def normalize_text(self, text: str) -> str:
        """
        Remplace les variantes connues dans un texte complet.
        """
        if not text or self._normalization_pattern is None:
            return text

        def replace(match: re.Match[str]) -> str:
            detected = match.group(0)

            return (
                self._alias_to_canonical.get(
                    detected.casefold()
                )
                or detected
            )

        return self._normalization_pattern.sub(replace, text)

    def expand_term(self, value: str) -> list[str]:
        """
        Retourne la forme canonique et toutes ses variantes connues.
        """
        canonical = self.find_alias(value)

        if canonical is None:
            cleaned = value.strip()
            return [cleaned] if cleaned else []

        variants = self._canonical_to_variants.get(
            canonical,
            [],
        )

        return self._deduplicate(
            [canonical, *variants]
        )

    def is_known(self, value: str) -> bool:
        return self.find_alias(value) is not None

    def canonical_terms(self) -> list[str]:
        return sorted(
            self._canonical_to_variants,
            key=str.casefold,
        )

    def statistics(self) -> dict[str, int]:
        return {
            "concepts": self.concept_count,
            "variants": self.variant_count,
            "aliases": len(self.aliases),
            "abbreviations": len(self.abbreviations),
            "synonym_groups": len(self.synonyms),
        }