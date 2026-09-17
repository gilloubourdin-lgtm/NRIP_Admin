from pathlib import Path

import pytest

from app.models.scientific_document import ScientificDocument
from app.services.document_parser import DocumentParser


@pytest.fixture
def parser() -> DocumentParser:
    return DocumentParser()


def test_parse_markdown_with_front_matter(parser):
    markdown = """---
document_id: NRIP-000
title: NRCave Research & Innovation Programme
document_type: Foundational Governance Document
status: Founding Draft
version: "0.1"
language: English
authors:
  - Gilles Bourdin
created: 2026
keywords:
  - knowledge
  - decision support
---

# NRCave Research & Innovation Programme

## Purpose

Scientific knowledge should endure.

## Scope

The programme studies knowledge convergence.
"""

    document = parser.parse_text(
        markdown,
        filename="NRIP-000_DNA.md",
        relative_path="00_governance/NRIP-000_DNA.md",
    )

    assert isinstance(document, ScientificDocument)
    assert document.document_id == "NRIP-000"
    assert document.title == "NRCave Research & Innovation Programme"
    assert document.document_type == "foundational governance document"
    assert document.status == "founding draft"
    assert document.version == "0.1"
    assert document.language == "english"
    assert document.authors == ["Gilles Bourdin"]
    assert document.year == 2026
    assert document.keywords == ["knowledge", "decision support"]
    assert document.filename == "NRIP-000_DNA.md"
    assert document.relative_path == "00_governance/NRIP-000_DNA.md"


def test_parse_uses_markdown_title_when_yaml_title_is_missing(parser):
    markdown = """---
document_id: NRIP-101
language: English
---

# Research Roadmap

Content.
"""

    document = parser.parse_text(
        markdown,
        filename="NRIP-101.md",
    )

    assert document.document_id == "NRIP-101"
    assert document.title == "Research Roadmap"


def test_parse_uses_filename_when_no_title_exists(parser):
    document = parser.parse_text(
        "Scientific content without a Markdown title.",
        filename="NRIP-420_Concept_Registry.md",
    )

    assert document.title == "NRIP-420_Concept_Registry"


def test_parse_extracts_sections(parser):
    markdown = """# Main title

Introduction text.

## Purpose

Purpose content.

### Scientific question

Question content.

## Methods

Methods content.
"""

    document = parser.parse_text(
        markdown,
        filename="document.md",
    )

    assert "Purpose" in document.sections
    assert "Scientific question" in document.sections
    assert "Methods" in document.sections
    assert "Purpose content." in document.sections["Purpose"]
    assert "Question content." in document.sections["Scientific question"]
    assert "Methods content." in document.sections["Methods"]


def test_parse_preserves_original_markdown(parser):
    markdown = "# Title\n\n**Important** scientific content."

    document = parser.parse_text(
        markdown,
        filename="document.md",
    )

    assert document.markdown == markdown


def test_parse_builds_plain_text(parser):
    markdown = """# Title

This is **important** scientific content.

- First item
- Second item
"""

    document = parser.parse_text(
        markdown,
        filename="document.md",
    )

    assert "Title" in document.plain_text
    assert "important" in document.plain_text
    assert "First item" in document.plain_text
    assert "**" not in document.plain_text


def test_parse_tolerates_unknown_yaml_metadata(parser):
    markdown = """---
document_id: NRIP-000
title: Document
short_title: DNA
review_cycle: Annual
unknown_future_field: value
---

# Document
"""

    document = parser.parse_text(
        markdown,
        filename="document.md",
    )

    assert document.document_id == "NRIP-000"
    assert document.title == "Document"


def test_parse_without_front_matter(parser):
    markdown = """# Scientific Document

## Results

Some results.
"""

    document = parser.parse_text(
        markdown,
        filename="scientific.md",
    )

    assert document.title == "Scientific Document"
    assert document.source_format == "markdown"
    assert "Results" in document.sections


def test_parse_file(parser, tmp_path: Path):
    path = tmp_path / "NRIP-500.md"
    path.write_text(
        "---\n"
        "document_id: NRIP-500\n"
        "title: File Parsing Test\n"
        "created: 2026\n"
        "---\n\n"
        "# File Parsing Test\n\n"
        "Content.",
        encoding="utf-8",
    )

    document = parser.parse_file(
        path,
        root=tmp_path,
    )

    assert document.document_id == "NRIP-500"
    assert document.title == "File Parsing Test"
    assert document.filename == "NRIP-500.md"
    assert document.relative_path == "NRIP-500.md"
    assert document.year == 2026
    assert document.file_modified_at is not None


def test_parse_rejects_non_string_text(parser):
    with pytest.raises(TypeError):
        parser.parse_text(123, filename="document.md")


def test_parse_infers_nrip_document_id_from_filename(parser):
    document = parser.parse_text(
        "Scientific content.",
        filename="NRIP-012_Scientific_Reading_Protocol.md",
    )

    assert document.document_id == "NRIP-012"


def test_parse_infers_scientific_domain_id_from_filename(parser):
    document = parser.parse_text(
        "Scientific domain content.",
        filename="SD-000_Index.md",
    )

    assert document.document_id == "SD-000"


def test_yaml_document_id_has_priority_over_filename(parser):
    markdown = """---
document_id: NRIP-999
title: Explicit ID
---

# Explicit ID
"""

    document = parser.parse_text(
        markdown,
        filename="NRIP-001_Other_Name.md",
    )

    assert document.document_id == "NRIP-999"
