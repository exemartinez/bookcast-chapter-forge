from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.fixed_page_classifier import FixedPageClassifier
from bookcast_chapter_forge.classifiers.heuristic_integrator_classifier import HeuristicIntegratorClassifier
from bookcast_chapter_forge.classifiers.index_chapter_classifier import IndexChapterClassifier
from bookcast_chapter_forge.classifiers.layout_aware_classifier import LayoutAwareClassifier
from bookcast_chapter_forge.classifiers.llm_enhanced_classifier import LLMEnhancedClassifier
from bookcast_chapter_forge.classifiers.model_assisted_classifier import ModelAssistedClassifier
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import RegexChapterClassifier
from bookcast_chapter_forge.classifiers.semantic_section_classifier import SemanticSectionClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult
from bookcast_chapter_forge.infrastructure.logging import EVENT_CLASSIFICATION_WARNING, EventLogger
from bookcast_chapter_forge.infrastructure.pdf_reader import PdfReaderAdapter
from bookcast_chapter_forge.services.adaptive_parser_wrapper import AdaptiveParserWrapper
from bookcast_chapter_forge.services.config_loader import ConfigLoader
from bookcast_chapter_forge.services.output_writer import OutputWriter


@dataclass(frozen=True)
class ProcessedBook:
    source: Path
    output_files: tuple[Path, ...]
    strategy: str
    chunk_count: int


class PdfParserService:
    """Coordinates config loading, PDF reading, classification, and output writing."""

    def __init__(
        self,
        config_loader: ConfigLoader | None = None,
        pdf_reader: PdfReaderAdapter | None = None,
        output_writer: OutputWriter | None = None,
        logger: EventLogger | None = None,
        classifiers: dict[str, ChapterClassifier] | None = None,
    ) -> None:
        """Build the service and register the available classification strategies."""
        self.config_loader = config_loader or ConfigLoader()
        self.pdf_reader = pdf_reader or PdfReaderAdapter()
        self.output_writer = output_writer or OutputWriter()
        self.logger = logger or EventLogger()
        self.adaptive_wrapper = AdaptiveParserWrapper(output_writer=self.output_writer, logger=self.logger)
        layout_classifier = LayoutAwareClassifier(logger=self.logger)
        self.classifiers = classifiers or {
            "fixed": FixedPageClassifier(),
            "regex": RegexChapterClassifier(),
            "index": IndexChapterClassifier(),
            "layout": layout_classifier,
            "semantic": SemanticSectionClassifier(),
            "model": ModelAssistedClassifier(),
            "heuristic": HeuristicIntegratorClassifier(logger=self.logger),
            "llm": LLMEnhancedClassifier(layout_classifier=layout_classifier, logger=self.logger),
        }

    def process(self, strategy: str, config_path: str | Path, input_path: str | Path | None = None, books_dir: str | Path | None = None) -> list[ProcessedBook]:
        """Process either one input PDF or every PDF in a directory with the selected strategy."""
        config = self.config_loader.load(config_path)
        if input_path:
            return [self.process_book(Path(input_path), strategy, config)]
        books_root = Path(books_dir or "books")
        pdf_paths = sorted(path for path in books_root.glob("*.pdf"))
        return [self.process_book(path, strategy, config) for path in pdf_paths]

    def process_book(self, path: Path, strategy: str, config) -> ProcessedBook:
        """Classify one book and write all resulting chunk PDFs to disk."""
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"{path} is not a PDF")
        self.logger.progress("read_pdf", path=str(path), strategy=strategy)
        book = self.pdf_reader.read_book(path)
        self._validate_book(book, strategy)
        actual_strategy = strategy
        if strategy == "adaptive":
            actual_strategy, result, _ = self.adaptive_wrapper.select_result(
                book,
                config,
                classify_with_strategy=lambda candidate_strategy: self.classifiers[candidate_strategy].classify(book, config),
                validate_result=self._validate_classification_result,
            )
        else:
            classifier = self.classifiers[strategy]
            result = classifier.classify(book, config)
            self._validate_classification_result(book, strategy, result)
        for warning in result.warnings:
            self.logger.warning(EVENT_CLASSIFICATION_WARNING, path=str(path), strategy=actual_strategy, message=warning)
        self.logger.progress("classification_complete", path=str(path), chunks=len(result.chunks), strategy=actual_strategy)
        if result.metadata:
            self.logger.progress("classification_metadata", path=str(path), strategy=actual_strategy, metadata=result.metadata)
        try:
            output_files = tuple(self.output_writer.write_book_chunks(book, result.chunks))
        except KeyboardInterrupt:
            self.logger.error("processing_interrupted", path=str(path))
            raise
        self.logger.info("write_complete", path=str(path), outputs=len(output_files))
        return ProcessedBook(source=path, output_files=output_files, strategy=actual_strategy, chunk_count=len(output_files))

    def _validate_book(self, book: BookDocument, strategy: str) -> None:
        """Reject empty or non-extractable documents before classification begins."""
        if book.page_count == 0:
            raise ValueError("The PDF has no pages")
        if strategy == "fixed":
            return
        if not any(text.strip() for text in book.page_texts):
            raise ValueError("The PDF does not contain extractable text")

    def _validate_classification_result(self, book: BookDocument, strategy: str, result: ClassificationResult) -> None:
        """Protect the writer from obviously invalid classifier outputs."""
        if strategy in {"fixed", "adaptive"}:
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
