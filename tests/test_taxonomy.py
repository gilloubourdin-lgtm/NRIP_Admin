import json
from pathlib import Path

import pytest

from app.models.taxonomy_node import TaxonomyNode
from app.services.taxonomy import (
    TaxonomyEngine,
    TaxonomyError,
)


def write_taxonomy(
    root: Path,
    filename: str,
    data: object,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / filename).write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


def test_taxonomy_node_creation():
    node = TaxonomyNode(
        id="organism.yeast",
        name="Levure",
        category="microorganism_group",
        aliases=["Yeast"],
    )

    assert node.id == "organism.yeast"
    assert node.name == "Levure"
    assert node.matches("yeast") is True


def test_taxonomy_node_rejects_empty_id():
    with pytest.raises(ValueError):
        TaxonomyNode(
            id="",
            name="Levure",
            category="microorganism",
        )


def test_taxonomy_node_rejects_empty_name():
    with pytest.raises(ValueError):
        TaxonomyNode(
            id="organism.yeast",
            name="",
            category="microorganism",
        )


def test_taxonomy_node_rejects_self_parent():
    with pytest.raises(ValueError):
        TaxonomyNode(
            id="organism",
            name="Organisme",
            category="root",
            parent_id="organism",
        )


def test_taxonomy_node_deduplicates_aliases():
    node = TaxonomyNode(
        id="analysis.gc_ms",
        name="GC-MS",
        category="analytical_method",
        aliases=["GCMS", "gcms", " GC MS "],
    )

    assert node.aliases == ["GCMS", "GC MS"]


def test_taxonomy_loads_default_resources():
    engine = TaxonomyEngine()

    assert engine.node_count > 0
    assert len(engine.loaded_files) >= 6
    assert engine.root_count > 0


@pytest.mark.parametrize(
    ("source", "expected_id"),
    [
        (
            "Brettanomyces",
            "organism.microorganism.yeast.brettanomyces",
        ),
        (
            "Brett",
            "organism.microorganism.yeast.brettanomyces",
        ),
        (
            "Dekkera",
            "organism.microorganism.yeast.brettanomyces",
        ),
        (
            "GCMS",
            "analysis.chromatography.gc_ms",
        ),
        (
            "Pinot Noir",
            "grape.red.pinot_noir",
        ),
        (
            "4 EP",
            "compound.aromatic.volatile_phenol.4_ep",
        ),
    ],
)
def test_find_by_name_or_alias(source, expected_id):
    engine = TaxonomyEngine()

    node = engine.find(source)

    assert node is not None
    assert node.id == expected_id


def test_find_by_id():
    engine = TaxonomyEngine()

    node = engine.find(
        "analysis.chromatography.gc_ms"
    )

    assert node is not None
    assert node.name == "GC-MS"


def test_find_is_case_insensitive():
    engine = TaxonomyEngine()

    assert engine.find("brett") is not None
    assert engine.find("BRETT") is not None


def test_unknown_concept_returns_none():
    engine = TaxonomyEngine()

    assert engine.find("Concept inconnu") is None
    assert engine.exists("Concept inconnu") is False


def test_require_raises_for_unknown_concept():
    engine = TaxonomyEngine()

    with pytest.raises(
        TaxonomyError,
        match="introuvable",
    ):
        engine.require("Concept inconnu")


def test_parent_lookup():
    engine = TaxonomyEngine()

    parent = engine.parent("Brettanomyces")

    assert parent is not None
    assert parent.name == "Levure"


def test_root_has_no_parent():
    engine = TaxonomyEngine()

    assert engine.parent("Organisme vivant") is None


def test_children_lookup():
    engine = TaxonomyEngine()

    children = engine.children("Levure")
    names = {node.name for node in children}

    assert "Brettanomyces" in names
    assert "Saccharomyces cerevisiae" in names


def test_path_from_root_to_node():
    engine = TaxonomyEngine()

    path = engine.path("Brettanomyces")

    assert [node.name for node in path] == [
        "Organisme vivant",
        "Microorganisme",
        "Levure",
        "Brettanomyces",
    ]


def test_ancestors_returns_nearest_parent_first():
    engine = TaxonomyEngine()

    ancestors = engine.ancestors("Brettanomyces")

    assert [node.name for node in ancestors] == [
        "Levure",
        "Microorganisme",
        "Organisme vivant",
    ]


def test_descendants_include_nested_nodes():
    engine = TaxonomyEngine()

    descendants = engine.descendants("Microorganisme")
    names = {node.name for node in descendants}

    assert "Levure" in names
    assert "Brettanomyces" in names
    assert "Oenococcus oeni" in names


def test_category_lookup():
    engine = TaxonomyEngine()

    assert (
        engine.category("GC-MS")
        == "analytical_method"
    )
    assert engine.category("Inconnu") is None


def test_nodes_in_category():
    engine = TaxonomyEngine()

    nodes = engine.nodes_in_category("grape_variety")
    names = {node.name for node in nodes}

    assert "Chasselas" in names
    assert "Pinot noir" in names


def test_search_uses_tags_and_descriptions():
    engine = TaxonomyEngine()

    results = engine.search("phénols volatils")
    names = {node.name for node in results}

    assert "Brettanomyces" in names


def test_statistics_are_consistent():
    engine = TaxonomyEngine()

    statistics = engine.statistics()

    assert statistics["nodes"] == engine.node_count
    assert statistics["roots"] == engine.root_count
    assert statistics["files"] == len(engine.loaded_files)
    assert "analytical_method" in statistics["categories"]


def test_missing_directory_raises_error(tmp_path: Path):
    missing = tmp_path / "missing"

    with pytest.raises(
        TaxonomyError,
        match="introuvable",
    ):
        TaxonomyEngine(missing)


def test_empty_directory_raises_error(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"
    taxonomy_root.mkdir()

    with pytest.raises(
        TaxonomyError,
        match="Aucun fichier JSON",
    ):
        TaxonomyEngine(taxonomy_root)


def test_invalid_json_raises_error(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"
    taxonomy_root.mkdir()

    (taxonomy_root / "invalid.json").write_text(
        "{ invalid",
        encoding="utf-8",
    )

    with pytest.raises(
        TaxonomyError,
        match="JSON invalide",
    ):
        TaxonomyEngine(taxonomy_root)


def test_json_root_must_be_list(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"

    write_taxonomy(
        taxonomy_root,
        "nodes.json",
        {"id": "root"},
    )

    with pytest.raises(
        TaxonomyError,
        match="liste JSON",
    ):
        TaxonomyEngine(taxonomy_root)


def test_duplicate_id_is_rejected(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"

    write_taxonomy(
        taxonomy_root,
        "one.json",
        [
            {
                "id": "root",
                "name": "Racine",
                "category": "root"
            }
        ],
    )
    write_taxonomy(
        taxonomy_root,
        "two.json",
        [
            {
                "id": "root",
                "name": "Autre racine",
                "category": "root"
            }
        ],
    )

    with pytest.raises(
        TaxonomyError,
        match="dupliqué",
    ):
        TaxonomyEngine(taxonomy_root)


def test_missing_parent_is_rejected(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"

    write_taxonomy(
        taxonomy_root,
        "nodes.json",
        [
            {
                "id": "child",
                "name": "Enfant",
                "category": "group",
                "parent_id": "missing"
            }
        ],
    )

    with pytest.raises(
        TaxonomyError,
        match="Parent introuvable",
    ):
        TaxonomyEngine(taxonomy_root)


def test_cycle_is_rejected(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"

    write_taxonomy(
        taxonomy_root,
        "nodes.json",
        [
            {
                "id": "node.a",
                "name": "A",
                "category": "group",
                "parent_id": "node.b"
            },
            {
                "id": "node.b",
                "name": "B",
                "category": "group",
                "parent_id": "node.a"
            }
        ],
    )

    with pytest.raises(
        TaxonomyError,
        match="Cycle détecté",
    ):
        TaxonomyEngine(taxonomy_root)


def test_ambiguous_alias_is_rejected(tmp_path: Path):
    taxonomy_root = tmp_path / "taxonomy"

    write_taxonomy(
        taxonomy_root,
        "nodes.json",
        [
            {
                "id": "node.a",
                "name": "Concept A",
                "category": "concept",
                "aliases": ["Même alias"]
            },
            {
                "id": "node.b",
                "name": "Concept B",
                "category": "concept",
                "aliases": ["Même alias"]
            }
        ],
    )

    with pytest.raises(
        TaxonomyError,
        match="ambigu",
    ):
        TaxonomyEngine(taxonomy_root)