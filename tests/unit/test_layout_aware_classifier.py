from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from bookcast_chapter_forge.classifiers.layout_aware_classifier import LayoutAwareClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ParserConfig


def test_layout_classifier_requires_optional_dependency(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pymupdf4llm":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    classifier = LayoutAwareClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("Chapter 1\nHello", "Chapter 2\nWorld"))
    config = ParserConfig(max_pages_per_chunk=10, layout_heading_patterns=(r"(?i)^chapter",))

    with pytest.raises(ValueError, match="pymupdf4llm"):
        classifier.classify(book, config)


def test_layout_classifier_emits_ordered_chunks(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pymupdf4llm":
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    classifier = LayoutAwareClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("Chapter 1\nHello", "text", "Chapter 2\nWorld", "text"))
    config = ParserConfig(max_pages_per_chunk=10, layout_heading_patterns=(r"(?i)^chapter",))

    result = classifier.classify(book, config)

    assert len(result.chunks) == 2
    assert result.chunks[0].start_page == 1
    assert result.chunks[1].start_page == 3
