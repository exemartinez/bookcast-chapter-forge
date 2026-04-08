from __future__ import annotations

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, chapter_start_pages
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig


class SemanticSectionClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "semantic"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        try:
            __import__("unstructured")
        except ModuleNotFoundError as exc:
            raise ValueError("semantic strategy requires optional dependency: unstructured") from exc

        patterns = config.semantic_title_patterns or config.regex_chapter_start_patterns
        starts = chapter_start_pages(book, patterns)
        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(chunks=chunks, metadata={"strategy": self.strategy_name, "evidence": "semantic"})

