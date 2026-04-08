from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from bookcast_chapter_forge.classifiers.semantic_section_classifier import SemanticSectionClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ParserConfig


def test_semantic_classifier_requires_optional_dependency(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "unstructured":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    classifier = SemanticSectionClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("Section One", "Body"))
    config = ParserConfig(max_pages_per_chunk=10, semantic_title_patterns=(r"(?i)^section",))

    with pytest.raises(ValueError, match="unstructured"):
        classifier.classify(book, config)
