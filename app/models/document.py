from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    relative_path: str
    filename: str
    title: str
    category: str
    line_count: int
    word_count: int
    size_bytes: int
    modified_at: str
    has_markdown_title: bool
    content_status: str
    structure_family: str

    @property
    def extension(self) -> str:
        return Path(self.filename).suffix.lower()