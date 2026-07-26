from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from app.models.taxonomy_node import TaxonomyNode


DEFAULT_TAXONOMY_ROOT = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "taxonomy"
)


class TaxonomyError(RuntimeError):
    """Erreur de chargement ou de validation de la taxonomie."""


class TaxonomyEngine:
    """
    Charge et expose une taxonomie scientifique hiérarchique.

    Le moteur assure :
    - le chargement de plusieurs fichiers JSON ;
    - la validation des identifiants et des parents ;
    - la recherche par identifiant, nom ou alias ;
    - la navigation parent/enfants ;
    - la reconstruction des chemins hiérarchiques ;
    - l'accès aux catégories et statistiques.
    """

    def __init__(
        self,
        taxonomy_root: Path | str | None = None,
    ) -> None:
        self.taxonomy_root = Path(
            taxonomy_root or DEFAULT_TAXONOMY_ROOT
        )

        self.nodes_by_id: dict[str, TaxonomyNode] = {}
        self.nodes_by_term: dict[str, TaxonomyNode] = {}
        self.children_by_parent: dict[
            str | None,
            list[TaxonomyNode],
        ] = defaultdict(list)
        self.nodes_by_category: dict[
            str,
            list[TaxonomyNode],
        ] = defaultdict(list)

        self.loaded_files: list[str] = []

        self.reload()

    def reload(self) -> None:
        self.nodes_by_id = {}
        self.nodes_by_term = {}
        self.children_by_parent = defaultdict(list)
        self.nodes_by_category = defaultdict(list)
        self.loaded_files = []

        nodes = self._load_all_nodes()
        self._build_indexes(nodes)
        self._validate_parent_references()
        self._validate_cycles()
        self._sort_indexes()

    def _load_all_nodes(self) -> list[TaxonomyNode]:
        if not self.taxonomy_root.exists():
            raise TaxonomyError(
                "Répertoire taxonomique introuvable : "
                f"{self.taxonomy_root}"
            )

        if not self.taxonomy_root.is_dir():
            raise TaxonomyError(
                "Le chemin taxonomique n'est pas un répertoire : "
                f"{self.taxonomy_root}"
            )

        files = sorted(self.taxonomy_root.glob("*.json"))

        if not files:
            raise TaxonomyError(
                "Aucun fichier JSON taxonomique trouvé dans "
                f"{self.taxonomy_root}"
            )

        result: list[TaxonomyNode] = []

        for path in files:
            result.extend(self._load_file(path))
            self.loaded_files.append(path.name)

        return result

    def _load_file(self, path: Path) -> list[TaxonomyNode]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except json.JSONDecodeError as exc:
            raise TaxonomyError(
                f"JSON invalide dans {path} : {exc}"
            ) from exc
        except OSError as exc:
            raise TaxonomyError(
                f"Impossible de lire {path} : {exc}"
            ) from exc

        if not isinstance(raw, list):
            raise TaxonomyError(
                f"La racine de {path} doit être une liste JSON."
            )

        nodes: list[TaxonomyNode] = []

        for index, item in enumerate(raw):
            try:
                node = TaxonomyNode.from_dict(
                    item,
                    source=path.name,
                )
            except (TypeError, ValueError) as exc:
                raise TaxonomyError(
                    f"Nœud invalide dans {path}, index {index} : "
                    f"{exc}"
                ) from exc

            nodes.append(node)

        return nodes

    def _build_indexes(
        self,
        nodes: Iterable[TaxonomyNode],
    ) -> None:
        for node in nodes:
            node_id_key = node.id.casefold()

            if node_id_key in self.nodes_by_id:
                existing = self.nodes_by_id[node_id_key]

                raise TaxonomyError(
                    "Identifiant taxonomique dupliqué : "
                    f"{node.id!r}, présent dans "
                    f"{existing.source!r} et {node.source!r}."
                )

            self.nodes_by_id[node_id_key] = node

            self._register_search_term(node.id, node)
            self._register_search_term(node.name, node)

            for alias in node.aliases:
                self._register_search_term(alias, node)

            self.children_by_parent[node.parent_id].append(node)
            self.nodes_by_category[
                node.category.casefold()
            ].append(node)

    def _register_search_term(
        self,
        term: str,
        node: TaxonomyNode,
    ) -> None:
        key = term.strip().casefold()

        if not key:
            return

        existing = self.nodes_by_term.get(key)

        if existing is not None and existing.id != node.id:
            raise TaxonomyError(
                f"Terme taxonomique ambigu {term!r} : "
                f"{existing.id!r} et {node.id!r}."
            )

        self.nodes_by_term[key] = node

    def _validate_parent_references(self) -> None:
        for node in self.nodes_by_id.values():
            if node.parent_id is None:
                continue

            if node.parent_id.casefold() not in self.nodes_by_id:
                raise TaxonomyError(
                    f"Parent introuvable pour {node.id!r} : "
                    f"{node.parent_id!r}."
                )

    def _validate_cycles(self) -> None:
        for node in self.nodes_by_id.values():
            visited: set[str] = set()
            current: TaxonomyNode | None = node

            while current is not None:
                key = current.id.casefold()

                if key in visited:
                    raise TaxonomyError(
                        "Cycle détecté dans la taxonomie autour de "
                        f"{current.id!r}."
                    )

                visited.add(key)

                if current.parent_id is None:
                    break

                current = self.nodes_by_id.get(
                    current.parent_id.casefold()
                )

    def _sort_indexes(self) -> None:
        for children in self.children_by_parent.values():
            children.sort(key=lambda node: node.name.casefold())

        for nodes in self.nodes_by_category.values():
            nodes.sort(key=lambda node: node.name.casefold())

    @staticmethod
    def _clean_query(value: str) -> str:
        return value.strip().casefold()

    def find(self, value: str) -> TaxonomyNode | None:
        """
        Recherche par identifiant, nom canonique ou alias.
        """
        key = self._clean_query(value)

        if not key:
            return None

        return (
            self.nodes_by_id.get(key)
            or self.nodes_by_term.get(key)
        )

    def require(self, value: str) -> TaxonomyNode:
        """
        Recherche un nœud et lève une erreur explicite s'il est absent.
        """
        node = self.find(value)

        if node is None:
            raise TaxonomyError(
                f"Concept taxonomique introuvable : {value!r}."
            )

        return node

    def exists(self, value: str) -> bool:
        return self.find(value) is not None

    def parent(
        self,
        value: str | TaxonomyNode,
    ) -> TaxonomyNode | None:
        node = (
            value
            if isinstance(value, TaxonomyNode)
            else self.find(value)
        )

        if node is None or node.parent_id is None:
            return None

        return self.nodes_by_id.get(
            node.parent_id.casefold()
        )

    def children(
        self,
        value: str | TaxonomyNode | None,
    ) -> list[TaxonomyNode]:
        if value is None:
            parent_id = None
        else:
            node = (
                value
                if isinstance(value, TaxonomyNode)
                else self.find(value)
            )

            if node is None:
                return []

            parent_id = node.id

        return list(
            self.children_by_parent.get(parent_id, [])
        )

    def descendants(
        self,
        value: str | TaxonomyNode,
    ) -> list[TaxonomyNode]:
        node = (
            value
            if isinstance(value, TaxonomyNode)
            else self.find(value)
        )

        if node is None:
            return []

        result: list[TaxonomyNode] = []
        stack = list(reversed(self.children(node)))

        while stack:
            current = stack.pop()
            result.append(current)

            current_children = self.children(current)
            stack.extend(reversed(current_children))

        return result

    def ancestors(
        self,
        value: str | TaxonomyNode,
    ) -> list[TaxonomyNode]:
        node = (
            value
            if isinstance(value, TaxonomyNode)
            else self.find(value)
        )

        if node is None:
            return []

        result: list[TaxonomyNode] = []
        current = self.parent(node)

        while current is not None:
            result.append(current)
            current = self.parent(current)

        return result

    def path(
        self,
        value: str | TaxonomyNode,
    ) -> list[TaxonomyNode]:
        """
        Retourne le chemin complet de la racine jusqu'au nœud.
        """
        node = (
            value
            if isinstance(value, TaxonomyNode)
            else self.find(value)
        )

        if node is None:
            return []

        return [
            *reversed(self.ancestors(node)),
            node,
        ]

    def category(self, value: str) -> str | None:
        node = self.find(value)
        return node.category if node else None

    def nodes_in_category(
        self,
        category: str,
    ) -> list[TaxonomyNode]:
        key = category.strip().casefold()

        if not key:
            return []

        return list(self.nodes_by_category.get(key, []))

    def roots(self) -> list[TaxonomyNode]:
        return self.children(None)

    def search(
        self,
        query: str,
    ) -> list[TaxonomyNode]:
        """
        Recherche textuelle simple dans les noms, alias, tags
        et descriptions.
        """
        searched = query.strip().casefold()

        if not searched:
            return []

        result: list[TaxonomyNode] = []

        for node in self.nodes_by_id.values():
            searchable = [
                node.id,
                node.name,
                node.description,
                *node.aliases,
                *node.tags,
            ]

            if any(
                searched in candidate.casefold()
                for candidate in searchable
                if candidate
            ):
                result.append(node)

        result.sort(key=lambda node: node.name.casefold())
        return result

    @property
    def node_count(self) -> int:
        return len(self.nodes_by_id)

    @property
    def root_count(self) -> int:
        return len(self.roots())

    def statistics(self) -> dict[str, Any]:
        category_counts = {
            category: len(nodes)
            for category, nodes in sorted(
                self.nodes_by_category.items()
            )
        }

        return {
            "nodes": self.node_count,
            "roots": self.root_count,
            "files": len(self.loaded_files),
            "search_terms": len(self.nodes_by_term),
            "categories": category_counts,
        }