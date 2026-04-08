from __future__ import annotations

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, chapter_start_pages
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig


class HeuristicIntegratorClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "heuristic"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        # Deterministic signal precedence: layout > semantic > regex fallback.
        weighted_patterns: list[tuple[float, tuple[str, ...], str]] = [
            (config.heuristic_signal_weights.get("layout", 3.0), config.layout_heading_patterns, "layout"),
            (config.heuristic_signal_weights.get("semantic", 2.0), config.semantic_title_patterns, "semantic"),
            (config.heuristic_signal_weights.get("regex", 1.0), config.regex_chapter_start_patterns, "regex"),
        ]

        scored_starts: dict[int, tuple[float, str]] = {}
        for weight, patterns, source in weighted_patterns:
            if not patterns:
                continue
            for page, title in chapter_start_pages(book, patterns):
                score, _ = scored_starts.get(page, (0.0, title))
                scored_starts[page] = (score + weight, title or source.title())

        ordered = sorted(
            ((page, score_title[1], score_title[0]) for page, score_title in scored_starts.items()),
            key=lambda item: (-item[2], item[0]),
        )
        starts = sorted([(page, title) for page, title, _ in ordered], key=lambda item: item[0])
        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(chunks=chunks, metadata={"strategy": self.strategy_name, "signals": len(starts)})

