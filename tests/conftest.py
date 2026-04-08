from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfWriter

from bookcast_chapter_forge.domain.entities import BookDocument


def create_blank_pdf(path: Path, pages: int) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


@pytest.fixture
def blank_pdf_factory(tmp_path: Path):
    def factory(name: str, pages: int) -> Path:
        return create_blank_pdf(tmp_path / name, pages)

    return factory


@pytest.fixture
def book_document_factory(tmp_path: Path):
    def factory(name: str, pages: list[str]) -> BookDocument:
        path = tmp_path / name
        create_blank_pdf(path, len(pages))
        return BookDocument(path=path, page_texts=tuple(pages), title=path.stem)

    return factory
