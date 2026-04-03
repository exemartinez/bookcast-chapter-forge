from __future__ import annotations

from pathlib import Path

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig
from bookcast_chapter_forge.services.output_writer import OutputWriter
from bookcast_chapter_forge.services.pdf_parser_service import PdfParserService


class StubClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "regex"

    def classify(self, book, config: ParserConfig) -> ClassificationResult:
        return ClassificationResult(chunks=(ChapterChunk(order=1, start_page=1, end_page=max(1, book.page_count)),))


class StubPdfReader:
    def read_book(self, path: Path) -> BookDocument:
        return BookDocument(path=path, page_texts=("Chapter 1",), title=path.stem)


def test_processes_single_pdf_in_fixed_mode(blank_pdf_factory, tmp_path: Path) -> None:
    pdf_path = blank_pdf_factory("single.pdf", 2)
    service = PdfParserService(output_writer=OutputWriter(output_dir=tmp_path / "out"))

    processed = service.process("fixed", "configs/config.yaml", input_path=pdf_path)

    assert processed[0].chunk_count == 2


def test_processes_all_pdfs_in_books_dir(blank_pdf_factory, tmp_path: Path) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    blank_pdf_factory("first.pdf", 1).replace(books_dir / "first.pdf")
    blank_pdf_factory("second.pdf", 1).replace(books_dir / "second.pdf")
    service = PdfParserService(
        output_writer=OutputWriter(output_dir=tmp_path / "out"),
        pdf_reader=StubPdfReader(),
        classifiers={"fixed": StubClassifier(), "regex": StubClassifier(), "index": StubClassifier()},
    )

    processed = service.process("regex", "configs/config.yaml", books_dir=books_dir)

    assert len(processed) == 2
