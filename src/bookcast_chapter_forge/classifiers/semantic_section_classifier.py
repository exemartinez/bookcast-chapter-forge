from __future__ import annotations

import re

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, chapter_start_pages, first_non_empty_line
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig

try:
    from unstructured.partition.text import partition_text as _partition_text
except ModuleNotFoundError:
    _partition_text =  None # The dependency is optional, so we can use the fallback.


class SemanticSectionClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "semantic"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        if _partition_text is None:
            raise ValueError("semantic strategy requires optional dependency: unstructured")

        patterns = config.semantic_title_patterns or config.regex_chapter_start_patterns
        try:
            starts = self._extract_semantic_starts(book, patterns, _partition_text)
        except Exception:
            # unstructured may require extra NLP assets at runtime; keep semantic strategy operational.
            starts = chapter_start_pages(book, patterns)
        if not starts:
            # Keep a safe fallback for documents where semantic partitioning yields no titles.
            starts = [(1, first_non_empty_line(book.page_texts[0]) or "Chapter 1")]
        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(chunks=chunks, metadata={"strategy": self.strategy_name, "evidence": "semantic"})

    def _extract_semantic_starts(self, book: BookDocument, patterns: tuple[str, ...], partition_text) -> list[tuple[int, str]]:
        starts: list[tuple[int, str]] = []
        seen: set[int] = set()

        for page_number, page_text in enumerate(book.page_texts, start=1):
            text = page_text.strip()
            if not text:
                continue
            elements = partition_text(text=text)
            for element in elements:
                category = str(getattr(element, "category", "") or element.__class__.__name__).lower()
                content = str(getattr(element, "text", "")).strip()
                if not content:
                    continue
                if "title" not in category and "header" not in category:
                    continue
                if patterns and not any(re.search(pattern, content) for pattern in patterns):
                    continue
                if page_number not in seen:
                    starts.append((page_number, content))
                    seen.add(page_number)
                break

        return starts

