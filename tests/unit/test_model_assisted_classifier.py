from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from bookcast_chapter_forge.classifiers.model_assisted_classifier import ModelAssistedClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ParserConfig


def test_model_strategy_requires_enable_flag() -> None:
    classifier = ModelAssistedClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("Chapter 1", "Body"))
    config = ParserConfig(max_pages_per_chunk=10, model_enabled=False)

    with pytest.raises(ValueError, match="model strategy is disabled"):
        classifier.classify(book, config)


def test_model_strategy_requires_langchain_dependency(monkeypatch) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "langchain":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    classifier = ModelAssistedClassifier()
    book = BookDocument(path=Path("book.pdf"), page_texts=("Chapter 1", "Body"))
    config = ParserConfig(max_pages_per_chunk=10, model_enabled=True, semantic_title_patterns=(r"(?i)^chapter",))

    with pytest.raises(ValueError, match="langchain"):
        classifier.classify(book, config)
