from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.fixed_page_classifier import FixedPageClassifier
from bookcast_chapter_forge.classifiers.heuristic_integrator_classifier import HeuristicIntegratorClassifier
from bookcast_chapter_forge.classifiers.index_chapter_classifier import IndexChapterClassifier
from bookcast_chapter_forge.classifiers.layout_aware_classifier import LayoutAwareClassifier
from bookcast_chapter_forge.classifiers.model_assisted_classifier import ModelAssistedClassifier
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import RegexChapterClassifier
from bookcast_chapter_forge.classifiers.semantic_section_classifier import SemanticSectionClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult
from bookcast_chapter_forge.infrastructure.logging import EventLogger
from bookcast_chapter_forge.infrastructure.pdf_reader import PdfReaderAdapter
from bookcast_chapter_forge.services.config_loader import ConfigLoader
from bookcast_chapter_forge.services.output_writer import OutputWriter


@dataclass(frozen=True)
class ProcessedBook:
    source: Path
    output_files: tuple[Path, ...]
    strategy: str
    chunk_count: int


class PdfParserService:
    def __init__(
        self,
        config_loader: ConfigLoader | None = None,
        pdf_reader: PdfReaderAdapter | None = None,
        output_writer: OutputWriter | None = None,
        logger: EventLogger | None = None,
        classifiers: dict[str, ChapterClassifier] | None = None,
    ) -> None:
        self.config_loader = config_loader or ConfigLoader()
        self.pdf_reader = pdf_reader or PdfReaderAdapter()
        self.output_writer = output_writer or OutputWriter()
        self.logger = logger or EventLogger()
        self.classifiers = classifiers or {
            "fixed": FixedPageClassifier(),
            "regex": RegexChapterClassifier(),
            "index": IndexChapterClassifier(),
            "layout": LayoutAwareClassifier(),
            "semantic": SemanticSectionClassifier(),
            "model": ModelAssistedClassifier(),
            "heuristic": HeuristicIntegratorClassifier(),
        }

    def process(self, strategy: str, config_path: str | Path, input_path: str | Path | None = None, books_dir: str | Path | None = None) -> list[ProcessedBook]:
        config = self.config_loader.load(config_path)
        if input_path:
            return [self.process_book(Path(input_path), strategy, config)]
        books_root = Path(books_dir or "books")
        pdf_paths = sorted(path for path in books_root.glob("*.pdf"))
        return [self.process_book(path, strategy, config) for path in pdf_paths]

    def process_book(self, path: Path, strategy: str, config) -> ProcessedBook:
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"{path} is not a PDF")
        classifier = self.classifiers[strategy]
        self.logger.progress("read_pdf", path=str(path), strategy=strategy)
        book = self.pdf_reader.read_book(path)
        self._validate_book(book, strategy)
        result = classifier.classify(book, config)
        self._validate_classification_result(book, strategy, result)
        self.logger.progress("classification_complete", path=str(path), chunks=len(result.chunks), strategy=strategy)
        try:
            output_files = tuple(self.output_writer.write_book_chunks(book, result.chunks))
        except KeyboardInterrupt:
            self.logger.error("processing_interrupted", path=str(path))
            raise
        self.logger.info("write_complete", path=str(path), outputs=len(output_files))
        return ProcessedBook(source=path, output_files=output_files, strategy=strategy, chunk_count=len(output_files))

    def _validate_book(self, book: BookDocument, strategy: str) -> None:
        if book.page_count == 0:
            raise ValueError("The PDF has no pages")
        if strategy == "fixed":
            return
        if not any(text.strip() for text in book.page_texts):
            raise ValueError("The PDF does not contain extractable text")

    def _validate_classification_result(self, book: BookDocument, strategy: str, result: ClassificationResult) -> None:
        if strategy == "fixed":
            return
        if not result.chunks:
            raise ValueError("The classifier did not return any chapter chunks")
        if any(chunk.page_count <= 0 for chunk in result.chunks):
            raise ValueError("The classifier returned an invalid zero-length chunk")
        if len(result.chunks) < 2 and book.page_count > max(20, len(result.chunks)):
            raise ValueError(f"The {strategy} strategy could not confidently identify generic chapter boundaries")
        self.logger.progress(
            "classification_confidence",
            path=str(book.path),
            strategy=strategy,
            chunks=len(result.chunks),
            pages=book.page_count,
        )
