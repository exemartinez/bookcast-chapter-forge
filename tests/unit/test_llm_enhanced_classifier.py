from __future__ import annotations

from pathlib import Path

import pytest

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.llm_enhanced_classifier import LLMEnhancedClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig


class StubLayoutClassifier(ChapterClassifier):
    """Provides predictable layout-derived chunks for LLM review tests."""

    @property
    def strategy_name(self) -> str:
        return "layout"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        return ClassificationResult(
            chunks=(
                ChapterChunk(order=1, start_page=1, end_page=2, title="Preface"),
                ChapterChunk(order=2, start_page=3, end_page=4, title="Chapter I"),
            )
        )


def test_llm_classifier_builds_review_packets_from_layout_candidates() -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(
        path=Path("book.pdf"),
        page_texts=("Preface", "More preface", "Chapter I", "Body"),
    )
    config = ParserConfig(max_pages_per_chunk=10, llm_review_window=1, llm_max_excerpt_chars=40)

    packet = classifier._build_review_packet(book, list(classifier._layout_classifier.classify(book, config).chunks), 1, config)

    assert packet.proposed_start_page == 3
    assert packet.previous_title == "Preface"
    assert "Chapter I" in packet.context_excerpt


def test_llm_classifier_requires_reachable_llama_server_runtime(monkeypatch) -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=("Chapter I", "Body", "Chapter II"))
    config = ParserConfig(max_pages_per_chunk=10)

    monkeypatch.setattr(
        classifier,
        "_invoke_chat_completion",
        lambda prompt, config: (_ for _ in ()).throw(ValueError("llm strategy requires a reachable local llama-server runtime")),
    )

    with pytest.raises(ValueError, match="llama-server"):
        classifier.classify(book, config)


def test_llm_classifier_sends_structured_local_evidence_not_full_document(monkeypatch) -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(
        path=Path("book.pdf"),
        page_texts=(
            "Preface\nA" * 50,
            "More preface\nB" * 50,
            "Chapter I\nImportant heading",
            "Body text",
        ),
    )
    config = ParserConfig(max_pages_per_chunk=10, llm_review_window=0, llm_max_excerpt_chars=25)
    prompts: list[str] = []

    def fake_invoke(prompt: str, config: ParserConfig) -> str:
        prompts.append(prompt)
        return '{"keep": true, "corrected_title": "Reviewed Chapter I", "rationale": "heading matches"}'

    monkeypatch.setattr(classifier, "_invoke_chat_completion", fake_invoke)

    result = classifier.classify(book, config)

    assert len(result.chunks) == 2
    assert result.chunks[0].title == "Reviewed Chapter I" or result.chunks[1].title == "Reviewed Chapter I"
    assert "A" * 200 not in prompts[0]
    assert "Proposed page range" in prompts[0]


def test_llm_classifier_rejects_non_llama_cpp_provider() -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=("Chapter I", "Body"))
    config = ParserConfig(max_pages_per_chunk=10, llm_provider="ollama")

    with pytest.raises(ValueError, match="provider=llama.cpp"):
        classifier.classify(book, config)


def test_llm_classifier_accepts_markdown_fenced_json() -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())

    decision = classifier._parse_review_decision(
        '```json\n{"keep": true, "corrected_title": "Chapter I", "rationale": "heading matches"}\n```',
        classifier._build_review_packet(
            BookDocument(path=Path("book.pdf"), page_texts=("Preface", "More", "Chapter I", "Body")),
            list(StubLayoutClassifier().classify(BookDocument(path=Path("book.pdf"), page_texts=("Preface", "More", "Chapter I", "Body")), ParserConfig(max_pages_per_chunk=10)).chunks),
            1,
            ParserConfig(max_pages_per_chunk=10),
        ),
    )

    assert decision.keep is True
    assert decision.corrected_title == "Chapter I"


def test_llm_classifier_falls_back_on_unparsable_model_output(monkeypatch) -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=("Preface", "More", "Chapter I", "Body"))
    config = ParserConfig(max_pages_per_chunk=10)

    monkeypatch.setattr(classifier, "_invoke_chat_completion", lambda prompt, config: "I think this should probably be kept.")

    result = classifier.classify(book, config)

    assert len(result.chunks) == 2
    assert any("fallback" in warning for warning in result.warnings)
