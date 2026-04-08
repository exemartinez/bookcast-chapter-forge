from __future__ import annotations

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig


class FixedPageClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "fixed"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        if config.max_pages_per_chunk <= 0:
            raise ValueError("max_pages_per_chunk must be greater than zero")
        chunks: list[ChapterChunk] = []
        order = 1
        for start in range(1, book.page_count + 1, config.max_pages_per_chunk):
            end = min(start + config.max_pages_per_chunk - 1, book.page_count)
            chunks.append(ChapterChunk(order=order, start_page=start, end_page=end))
            order += 1
        return ClassificationResult(chunks=tuple(chunks), metadata={"strategy": self.strategy_name})
