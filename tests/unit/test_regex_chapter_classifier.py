from __future__ import annotations

import pytest

from bookcast_chapter_forge.classifiers.regex_chapter_classifier import RegexChapterClassifier
from bookcast_chapter_forge.domain.entities import ParserConfig


def _config() -> ParserConfig:
    return ParserConfig(
        max_pages_per_chunk=2,
        regex_english_patterns=("(?i)the",),
        regex_chapter_start_patterns=("(?i)^chapter\\s+\\d+",),
        regex_book_start_patterns=("(?i)^preface",),
    )


def test_detects_chapter_boundaries(book_document_factory) -> None:
    book = book_document_factory(
        "chaptered.pdf",
        [
            "Preface\nThe story begins",
            "Chapter 1\nThe first section",
            "Body text",
            "Chapter 2\nThe second section",
            "Closing text",
        ],
    )

    result = RegexChapterClassifier().classify(book, _config())

    assert [(chunk.start_page, chunk.end_page) for chunk in result.chunks] == [(1, 1), (2, 3), (4, 5)]


def test_rejects_non_english_documents(book_document_factory) -> None:
    book = book_document_factory("foreign.pdf", ["Bonjour", "Chapitre 1"])

    with pytest.raises(ValueError):
        RegexChapterClassifier().classify(book, _config())
