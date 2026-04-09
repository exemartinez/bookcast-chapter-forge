from __future__ import annotations

from pathlib import Path

from bookcast_chapter_forge.classifiers.heuristic_integrator_classifier import HeuristicIntegratorClassifier
from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig


class StubSignalClassifier(ChapterClassifier):
    def __init__(self, strategy_name: str, starts: tuple[int, ...]) -> None:
        self._strategy_name = strategy_name
        self._starts = starts

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        return ClassificationResult(
            chunks=tuple(
                ChapterChunk(order=index, start_page=page, end_page=page, title=f"{self._strategy_name}-{page}")
                for index, page in enumerate(self._starts, start=1)
            )
        )


def test_heuristic_integrator_builds_non_overlapping_chunks() -> None:
    classifier = HeuristicIntegratorClassifier()
    book = BookDocument(
        path=Path("book.pdf"),
        page_texts=(
            "Chapter 1\nIntro",
            "Body",
            "Part 2\nMiddle",
            "Body",
            "Chapter 3\nEnd",
        ),
    )
    config = ParserConfig(
        max_pages_per_chunk=10,
        layout_heading_patterns=(r"(?i)^chapter",),
        semantic_title_patterns=(r"(?i)^part",),
        regex_chapter_start_patterns=(r"(?i)^chapter",),
        heuristic_signal_weights={"layout": 3.0, "semantic": 2.0, "regex": 1.0},
    )

    result = classifier.classify(book, config)

    assert len(result.chunks) >= 2
    assert all(chunk.start_page <= chunk.end_page for chunk in result.chunks)
    assert list(chunk.start_page for chunk in result.chunks) == sorted(chunk.start_page for chunk in result.chunks)


def test_heuristic_integrator_prefers_higher_weighted_pages(monkeypatch) -> None:
    classifier = HeuristicIntegratorClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("one", "two", "three"))
    config = ParserConfig(
        max_pages_per_chunk=10,
        heuristic_signal_weights={"layout": 3.0, "semantic": 2.0, "regex": 1.0},
    )

    monkeypatch.setattr(
        classifier,
        "_strategy_sources",
        lambda _config: (
            ("layout", 3.0, StubSignalClassifier("layout", (2,))),
            ("semantic", 2.0, StubSignalClassifier("semantic", (2, 3))),
            ("regex", 1.0, StubSignalClassifier("regex", (1,))),
        ),
    )

    result = classifier.classify(book, config)

    assert [chunk.start_page for chunk in result.chunks] == [1, 2, 3]
    assert result.chunks[1].title == "layout-2"
