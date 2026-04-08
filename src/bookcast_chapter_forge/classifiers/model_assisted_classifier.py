from __future__ import annotations

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, chapter_start_pages
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig


class ModelAssistedClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "model"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        if not config.model_enabled:
            raise ValueError("model strategy is disabled; set model.enabled=true in config")
        try:
            __import__("langchain")
        except ModuleNotFoundError as exc:
            raise ValueError("model strategy requires optional dependency: langchain") from exc

        # Model-assisted mode ranks pre-built candidates; it does not consume full raw documents.
        patterns = config.semantic_title_patterns or config.regex_chapter_start_patterns
        starts = chapter_start_pages(book, patterns)
        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(chunks=chunks, metadata={"strategy": self.strategy_name, "evidence": "model-ranked-candidates"})

