from __future__ import annotations

from pathlib import Path

from bookcast_chapter_forge.classifiers.heuristic_integrator_classifier import HeuristicIntegratorClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ParserConfig


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
