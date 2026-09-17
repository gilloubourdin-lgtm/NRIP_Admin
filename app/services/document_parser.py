from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any

import yaml

from app.models.scientific_document import ScientificDocument


FRONT_MATTER_PATTERN = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
    flags=re.DOTALL,
)

HEADING_PATTERN = re.compile(
    r"^(#{1,6})\s+(.+?)\s*$"
)

MARKDOWN_DECORATION_PATTERN = re.compile(
    r"[*_`~]"
)

MARKDOWN_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\([^)]+\)"
)

DOCUMENT_ID_FILENAME_PATTERN = re.compile(
    r"^(NRIP|SD)-(\d{3})(?:[_\-.]|$)",
    flags=re.IGNORECASE,
)


class DocumentParserError(RuntimeError):
    """Erreur liée au parsing d'un document scientifique."""


class DocumentParser:
    """
    Transforme un document Markdown en ScientificDocument.

    V1 reste volontairement limitée à la structure documentaire.
    L'extraction d'entités et la construction du graphe appartiennent
    à des étapes ultérieures du pipeline.
    """

    def parse_text(
        self,
        text: str,
        *,
        filename: str = "",
        relative_path: str = "",
    ) -> ScientificDocument:
        if not isinstance(text, str):
            raise TypeError(
                "DocumentParser.parse_text attend une chaîne de caractères."
            )

        metadata, body = self._split_front_matter(text)

        markdown_title = self._extract_markdown_title(body)
        filename_title = (
            Path(filename).stem
            if filename
            else ""
        )

        title = self._as_string(
            metadata.get("title")
        ) or markdown_title or filename_title

        document_id = (
            self._as_string(
                metadata.get("document_id")
            )
            or self._extract_document_id_from_filename(
                filename
            )
        )

        document_kwargs: dict[str, Any] = {
            "title": title,
            "abstract": self._optional_string(
                metadata.get("abstract")
            ),
            "language": self._as_string(
                metadata.get("language")
            ) or "unknown",
            "document_type": self._as_string(
                metadata.get("document_type")
            ) or "unknown",
            "status": self._as_string(
                metadata.get("status")
            ) or "active",
            "version": self._optional_string(
                metadata.get("version")
            ),
            "authors": self._as_string_list(
                metadata.get("authors")
            ),
            "institutions": self._as_string_list(
                metadata.get("institutions")
            ),
            "year": self._extract_year(metadata),
            "journal": self._optional_string(
                metadata.get("journal")
            ),
            "doi": self._optional_string(
                metadata.get("doi")
            ),
            "projects": self._extract_projects(metadata),
            "funding_sources": self._as_string_list(
                metadata.get("funding_sources")
            ),
            "filename": filename,
            "relative_path": relative_path,
            "source_format": "markdown",
            "markdown": text,
            "plain_text": self._build_plain_text(body),
            "sections": self._extract_sections(body),
            "keywords": self._as_string_list(
                metadata.get("keywords")
            ),
            "topics": self._as_string_list(
                metadata.get("topics")
            ),
        }

        if document_id:
            document_kwargs["document_id"] = document_id

        return ScientificDocument(**document_kwargs)

    def parse_file(
        self,
        path: Path | str,
        *,
        root: Path | str | None = None,
    ) -> ScientificDocument:
        file_path = Path(path).expanduser().resolve()

        if not file_path.exists():
            raise DocumentParserError(
                f"Le document est introuvable : {file_path}"
            )

        if not file_path.is_file():
            raise DocumentParserError(
                f"Le chemin n'est pas un fichier : {file_path}"
            )

        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise DocumentParserError(
                f"Impossible de lire le document : {file_path}"
            ) from exc

        if root is not None:
            root_path = Path(root).expanduser().resolve()

            try:
                relative_path = file_path.relative_to(
                    root_path
                ).as_posix()
            except ValueError:
                relative_path = file_path.name
        else:
            relative_path = file_path.name

        document = self.parse_text(
            text,
            filename=file_path.name,
            relative_path=relative_path,
        )

        stat = file_path.stat()

        document.file_created_at = datetime.fromtimestamp(
            stat.st_ctime
        ).astimezone()

        document.file_modified_at = datetime.fromtimestamp(
            stat.st_mtime
        ).astimezone()

        return document

    def _split_front_matter(
        self,
        text: str,
    ) -> tuple[dict[str, Any], str]:
        match = FRONT_MATTER_PATTERN.match(text)

        if match is None:
            return {}, text

        try:
            loaded = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise DocumentParserError(
                "Le front matter YAML est invalide."
            ) from exc

        if loaded is None:
            metadata: dict[str, Any] = {}
        elif isinstance(loaded, dict):
            metadata = loaded
        else:
            raise DocumentParserError(
                "Le front matter YAML doit contenir un mapping."
            )

        body = text[match.end():]

        return metadata, body

    @staticmethod
    def _extract_markdown_title(text: str) -> str:
        for line in text.splitlines():
            match = HEADING_PATTERN.match(line)

            if match and len(match.group(1)) == 1:
                return match.group(2).strip()

        return ""

    @staticmethod
    def _extract_sections(text: str) -> dict[str, str]:
        sections: dict[str, str] = {}

        current_title: str | None = None
        current_lines: list[str] = []

        def store_current() -> None:
            if current_title is None:
                return

            content = "\n".join(
                current_lines
            ).strip()

            if current_title in sections and content:
                previous = sections[current_title]

                sections[current_title] = (
                    f"{previous}\n\n{content}".strip()
                )
            else:
                sections[current_title] = content

        for line in text.splitlines():
            match = HEADING_PATTERN.match(line)

            if match:
                level = len(match.group(1))

                if level >= 2:
                    store_current()
                    current_title = match.group(2).strip()
                    current_lines = []
                    continue

                if level == 1 and current_title is not None:
                    current_lines.append(line)

                continue

            if current_title is not None:
                current_lines.append(line)

        store_current()

        return sections

    @staticmethod
    def _build_plain_text(text: str) -> str:
        lines: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            heading = HEADING_PATTERN.match(line)

            if heading:
                line = heading.group(2).strip()

            line = re.sub(
                r"^\s*[-+*]\s+",
                "",
                line,
            )

            line = MARKDOWN_LINK_PATTERN.sub(
                r"\1",
                line,
            )

            line = MARKDOWN_DECORATION_PATTERN.sub(
                "",
                line,
            )

            line = line.strip()

            if line:
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def _as_string(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @classmethod
    def _optional_string(
        cls,
        value: Any,
    ) -> str | None:
        cleaned = cls._as_string(value)

        return cleaned or None

    @classmethod
    def _as_string_list(
        cls,
        value: Any,
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, (list, tuple, set)):
            return [
                cleaned
                for item in value
                if (cleaned := cls._as_string(item))
            ]

        cleaned = cls._as_string(value)

        return [cleaned] if cleaned else []

    @staticmethod
    def _extract_document_id_from_filename(
        filename: str,
    ) -> str:
        if not filename:
            return ""

        match = DOCUMENT_ID_FILENAME_PATTERN.match(
            Path(filename).stem
        )

        if match is None:
            return ""

        prefix = match.group(1).upper()
        number = match.group(2)

        return f"{prefix}-{number}"

    @classmethod
    def _extract_year(
        cls,
        metadata: dict[str, Any],
    ) -> int | None:
        value = metadata.get(
            "year",
            metadata.get("created"),
        )

        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, datetime):
            return value.year

        cleaned = cls._as_string(value)

        match = re.search(
            r"\b(1[5-9]\d{2}|20\d{2}|21\d{2}|2200)\b",
            cleaned,
        )

        if match is None:
            return None

        return int(match.group(1))

    @classmethod
    def _extract_projects(
        cls,
        metadata: dict[str, Any],
    ) -> list[str]:
        projects = cls._as_string_list(
            metadata.get("projects")
        )

        programme = cls._as_string(
            metadata.get("programme")
        )

        if programme:
            projects.append(programme)

        return projects
