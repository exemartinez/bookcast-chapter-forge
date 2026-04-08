from __future__ import annotations

from bookcast_chapter_forge.classifiers.fixed_page_classifier import FixedPageClassifier
from bookcast_chapter_forge.domain.entities import ParserConfig


def test_generates_sequential_fixed_page_chunks(book_document_factory) -> None:
    book = book_document_factory("sample.pdf", ["", "", "", "", ""])

    result = FixedPageClassifier().classify(book, ParserConfig(max_pages_per_chunk=2))

    assert [(chunk.start_page, chunk.end_page) for chunk in result.chunks] == [(1, 2), (3, 4), (5, 5)]
