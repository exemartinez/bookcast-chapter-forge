from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from bookcast_chapter_forge.classifiers.semantic_section_classifier import SemanticSectionClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ParserConfig


def test_semantic_classifier_requires_optional_dependency(monkeypatch) -> None:
    monkeypatch.setattr("bookcast_chapter_forge.classifiers.semantic_section_classifier._partition_text", None)
    classifier = SemanticSectionClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("Section One", "Body"))
    config = ParserConfig(max_pages_per_chunk=10, semantic_title_patterns=(r"(?i)^section",))

    with pytest.raises(ValueError, match="unstructured"):
        classifier.classify(book, config)


def test_semantic_classifier_uses_title_elements(monkeypatch) -> None:
    class FakeElement:
        def __init__(self, text: str, category: str) -> None:
            self.text = text
            self.category = category

    def fake_partition_text(*, text: str):
        if "Chapter 1" in text:
            return [FakeElement("Chapter 1", "Title")]
        if "Chapter 2" in text:
            return [FakeElement("Chapter 2", "Title")]
        return [FakeElement("Body paragraph", "NarrativeText")]

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "unstructured.partition.text":
            class FakeModule:
                partition_text = staticmethod(fake_partition_text)
            return FakeModule()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    classifier = SemanticSectionClassifier()
    book = BookDocument(
        path=Path("book.pdf"),
        page_texts=("Chapter 1\nIntro", "Body text", "Chapter 2\nDetails", "Tail"),
    )
    config = ParserConfig(max_pages_per_chunk=10, semantic_title_patterns=(r"(?i)^chapter",))

    result = classifier.classify(book, config)

    assert len(result.chunks) == 2
    assert result.chunks[0].start_page == 1
    assert result.chunks[1].start_page == 3
