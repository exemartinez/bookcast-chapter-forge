from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from bookcast_chapter_forge.domain.entities import ChapterChunk
from bookcast_chapter_forge.services.output_writer import OutputWriter


def test_writes_pdf_chunks_atomically(blank_pdf_factory, book_document_factory, tmp_path: Path) -> None:
    pdf_path = blank_pdf_factory("source.pdf", 3)
    book = book_document_factory("source.pdf", ["", "", ""])
    book = type(book)(path=pdf_path, page_texts=book.page_texts, title=book.title)
    writer = OutputWriter(output_dir=tmp_path / "out")

    outputs = writer.write_book_chunks(book, (ChapterChunk(1, 1, 2), ChapterChunk(2, 3, 3)))

    assert len(outputs) == 2
    assert len(PdfReader(str(outputs[0])).pages) == 2
    assert len(PdfReader(str(outputs[1])).pages) == 1


def test_sanitizes_and_truncates_titles() -> None:
    writer = OutputWriter(output_dir="output")

    filename = writer.filename_for_chunk(
        book=type("Book", (), {"stem": "My Book"})(),
        chunk=ChapterChunk(order=1, start_page=1, end_page=2, title="Chapter: Alpha/Beta"),
    )

    assert filename == "My-Book-001-Chapter-Alpha.pdf"


def test_preserves_chapter_numerals_in_filename_slug() -> None:
    writer = OutputWriter(output_dir="output")

    filename = writer.filename_for_chunk(
        book=type("Book", (), {"stem": "My Book"})(),
        chunk=ChapterChunk(order=7, start_page=1, end_page=2, title="Chapter VII: Prompting with LangChain"),
    )

    assert filename == "My-Book-007-Chapter-VII.pdf"


def test_cleans_up_temp_output_on_failure(blank_pdf_factory, book_document_factory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = blank_pdf_factory("source.pdf", 2)
    book = book_document_factory("source.pdf", ["", ""])
    book = type(book)(path=pdf_path, page_texts=book.page_texts, title=book.title)
    writer = OutputWriter(output_dir=tmp_path / "out")

    def broken_move(*args, **kwargs):
        raise RuntimeError("move failed")

    monkeypatch.setattr("bookcast_chapter_forge.services.output_writer.shutil.move", broken_move)

    with pytest.raises(RuntimeError):
        writer.write_book_chunks(book, (ChapterChunk(1, 1, 2),))

    assert not any(tmp_path.glob("bookcast-*"))
