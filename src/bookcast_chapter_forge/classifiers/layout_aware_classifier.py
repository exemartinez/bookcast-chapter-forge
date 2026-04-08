from __future__ import annotations

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, chapter_start_pages
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig


class LayoutAwareClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "layout"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        try:
            __import__("pymupdf4llm")
        except ModuleNotFoundError as exc:
            raise ValueError("layout strategy requires optional dependency: pymupdf4llm") from exc

        patterns = config.layout_heading_patterns or config.regex_chapter_start_patterns
        starts = chapter_start_pages(book, patterns)
        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(chunks=chunks, metadata={"strategy": self.strategy_name, "evidence": "layout"})

