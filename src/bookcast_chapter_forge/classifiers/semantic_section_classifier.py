from __future__ import annotations

import re
from typing import Callable

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig

_UNSET = object()
_partition_text: Callable[..., list[object]] | None | object = _UNSET


class SemanticSectionClassifier(ChapterClassifier):
    """Infer chapter starts from semantic title/header elements exposed by unstructured."""

    @property
    def strategy_name(self) -> str:
        return "semantic"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        """Build chunks from pages whose semantic elements look like section-title boundaries."""
        partition_text = self._require_partition_text()
        patterns = config.semantic_title_patterns or config.regex_chapter_start_patterns
        if not patterns:
            raise ValueError("semantic strategy requires title patterns")

        starts, warnings = self._extract_semantic_starts(book, patterns, partition_text)
        if not starts:
            raise ValueError("semantic strategy could not identify semantic section boundaries")

        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(
            chunks=chunks,
            warnings=tuple(warnings),
            metadata={"strategy": self.strategy_name, "evidence": "semantic-elements", "signals": len(starts)},
        )

    def _require_partition_text(self) -> Callable[..., list[object]]:
        """Fail cleanly when the optional semantic partitioner is not installed."""
        if _partition_text is None:
            raise ValueError("semantic strategy requires optional dependency: unstructured")
        if _partition_text is not _UNSET:
            return _partition_text
        try:
            module = __import__("unstructured.partition.text", fromlist=["partition_text"])
        except ModuleNotFoundError as exc:
            raise ValueError("semantic strategy requires optional dependency: unstructured") from exc

        return module.partition_text

    def _extract_semantic_starts(
        self,
        book: BookDocument,
        patterns: tuple[str, ...],
        partition_text: Callable[..., list[object]],
    ) -> tuple[list[tuple[int, str]], list[str]]:
        """Collect title/header elements from each page and keep those matching configured chapter patterns."""
        starts: list[tuple[int, str]] = []
        warnings: list[str] = []
        seen_pages: set[int] = set()

        for page_number, page_text in enumerate(book.page_texts, start=1):
            text = page_text.strip()
            if not text:
                continue
            try:
                elements = partition_text(text=text)
            except Exception:
                warnings.append(f"semantic partition failed on page {page_number}")
                continue

            for element in elements:
                category = str(getattr(element, "category", "") or element.__class__.__name__).lower()
                content = str(getattr(element, "text", "")).strip()
                if not content:
                    continue
                if "title" not in category and "header" not in category:
                    continue
                if not any(re.search(pattern, content) for pattern in patterns):
                    continue
                if page_number not in seen_pages:
                    starts.append((page_number, content))
                    seen_pages.add(page_number)
                break

        return starts, warnings
