from __future__ import annotations

import pytest

from bookcast_chapter_forge.classifiers.index_chapter_classifier import IndexChapterClassifier
from bookcast_chapter_forge.domain.entities import ParserConfig


def _config() -> ParserConfig:
    return ParserConfig(
        max_pages_per_chunk=2,
        index_title_patterns=("(?i)^contents$",),
        index_entry_patterns=("^(?P<title>.+?)[. ]+(?P<page>\\d+)$",),
    )


def test_parses_index_entries_and_applies_offset(book_document_factory) -> None:
    book = book_document_factory(
        "indexed.pdf",
        [
            "Cover",
            "Contents\nChapter One ... 1\nChapter Two ... 3",
            "Intro",
            "Chapter One\nHello",
            "Body",
            "Chapter Two\nWorld",
            "End",
        ],
    )

    result = IndexChapterClassifier().classify(book, _config())

    assert [(chunk.title, chunk.start_page, chunk.end_page) for chunk in result.chunks] == [
        ("Chapter One", 4, 5),
        ("Chapter Two", 6, 7),
    ]
    assert result.metadata["page_offset"] == 3


def test_fails_when_no_index_page_is_found(book_document_factory) -> None:
    book = book_document_factory("no-index.pdf", ["Cover", "Chapter One"])

    with pytest.raises(ValueError):
        IndexChapterClassifier().classify(book, _config())
