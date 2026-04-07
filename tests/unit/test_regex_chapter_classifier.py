from __future__ import annotations

import inspect
import pytest

import bookcast_chapter_forge.classifiers.regex_chapter_classifier as regex_module
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import RegexChapterClassifier
from bookcast_chapter_forge.domain.entities import ParserConfig


def _config() -> ParserConfig:
    return ParserConfig(
        max_pages_per_chunk=2,
        regex_english_patterns=("(?i)the", "(?i)and", "(?i)with"),
        regex_chapter_start_patterns=("(?i)^chapter\\s+\\w+", "(?i)^part\\s+\\w+", "(?i)^section\\s+\\w+"),
        regex_book_start_patterns=("(?i)^preface", "(?i)^introduction"),
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


def test_detects_generic_part_and_section_boundaries(book_document_factory) -> None:
    book = book_document_factory(
        "generic.pdf",
        [
            "Introduction\nThis is the opening.",
            "Body text",
            "Part I\nFoundations",
            "More body text",
            "Section 2\nPutting it to work",
            "Closing body text",
        ],
    )

    result = RegexChapterClassifier().classify(book, _config())

    assert [(chunk.title, chunk.start_page, chunk.end_page) for chunk in result.chunks] == [
        ("Introduction", 1, 2),
        ("Part I", 3, 4),
        ("Section 2", 5, 6),
    ]


def test_default_regex_classifier_has_no_domain_specific_title_catalog() -> None:
    source = inspect.getsource(regex_module)

    assert "KNOWN_BOOK_TITLES" not in source
    assert "genesis" not in source.lower()
