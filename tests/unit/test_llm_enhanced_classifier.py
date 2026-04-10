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
        return '{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Reviewed Chapter I", "rationale": "heading matches"}'

    monkeypatch.setattr(classifier, "_invoke_chat_completion", fake_invoke)

    result = classifier.classify(book, config)

    assert len(result.chunks) == 1
    assert result.chunks[0].title == "Reviewed Chapter I"
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
        '```json\n{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Chapter I", "rationale": "heading matches"}\n```',
        classifier._build_review_packet(
            BookDocument(path=Path("book.pdf"), page_texts=("Preface", "More", "Chapter I", "Body")),
            list(StubLayoutClassifier().classify(BookDocument(path=Path("book.pdf"), page_texts=("Preface", "More", "Chapter I", "Body")), ParserConfig(max_pages_per_chunk=10)).chunks),
            1,
            ParserConfig(max_pages_per_chunk=10),
        ),
    )

    assert decision.keep is True
    assert decision.page_kind == "body_chapter_start"
    assert decision.corrected_title == "Chapter I"


def test_llm_classifier_falls_back_on_unparsable_model_output(monkeypatch) -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=("Preface", "More", "Chapter I", "Body"))
    config = ParserConfig(max_pages_per_chunk=10)

    monkeypatch.setattr(classifier, "_invoke_chat_completion", lambda prompt, config: "I think this should probably be kept.")

    result = classifier.classify(book, config)

    assert len(result.chunks) == 2
    assert any("fallback" in warning for warning in result.warnings)


def test_llm_classifier_reviews_only_suspicious_cuts(monkeypatch) -> None:
    class ManyChunkLayoutClassifier(ChapterClassifier):
        @property
        def strategy_name(self) -> str:
            return "layout"

        def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
            return ClassificationResult(
                chunks=(
                    ChapterChunk(order=1, start_page=1, end_page=5, title="Preface"),
                    ChapterChunk(order=2, start_page=20, end_page=30, title="Chapter I"),
                    ChapterChunk(order=3, start_page=40, end_page=50, title="Chapter II"),
                    ChapterChunk(order=4, start_page=60, end_page=70, title="Chapter III"),
                )
            )

    classifier = LLMEnhancedClassifier(layout_classifier=ManyChunkLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=tuple(f"Page {index}" for index in range(1, 80)))
    config = ParserConfig(max_pages_per_chunk=10)
    calls: list[str] = []

    def fake_invoke(prompt: str, config: ParserConfig) -> str:
        calls.append(prompt)
        if "Proposed title: Preface" in prompt:
            return '{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Reviewed Preface", "rationale": "ok"}'
        return '{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Reviewed Chapter I", "rationale": "ok"}'

    monkeypatch.setattr(classifier, "_invoke_chat_completion", fake_invoke)

    result = classifier.classify(book, config)

    assert len(result.chunks) == 4
    assert len(calls) == 2


def test_llm_classifier_rejects_non_body_page_kinds(monkeypatch) -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=("Contents", "Summary", "Chapter I", "Body"))
    config = ParserConfig(max_pages_per_chunk=10)
    responses = iter(
        (
            '{"page_kind": "toc", "keep": false, "corrected_title": "Preface", "rationale": "toc page"}',
            '{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Chapter I", "rationale": "body chapter"}',
        )
    )

    monkeypatch.setattr(classifier, "_invoke_chat_completion", lambda prompt, config: next(responses))

    result = classifier.classify(book, config)

    assert len(result.chunks) == 1
    assert result.chunks[0].title == "Chapter I"
    assert any("rejected cut starting at page 1" in warning for warning in result.warnings)


def test_llm_classifier_discards_leading_non_body_chunks(monkeypatch) -> None:
    class LeadingNoiseLayoutClassifier(ChapterClassifier):
        @property
        def strategy_name(self) -> str:
            return "layout"

        def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
            return ClassificationResult(
                chunks=(
                    ChapterChunk(order=1, start_page=1, end_page=2, title="Contents"),
                    ChapterChunk(order=2, start_page=3, end_page=4, title="Chapter I"),
                    ChapterChunk(order=3, start_page=10, end_page=18, title="Chapter II"),
                )
            )

    classifier = LLMEnhancedClassifier(layout_classifier=LeadingNoiseLayoutClassifier())
    book = BookDocument(path=Path("book.pdf"), page_texts=tuple(f"Page {index}" for index in range(1, 25)))
    config = ParserConfig(max_pages_per_chunk=10)
    responses = iter(
        (
            '{"page_kind": "chapter_summary", "keep": false, "corrected_title": "Contents", "rationale": "summary spread"}',
            '{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Chapter I", "rationale": "real chapter start"}',
            '{"page_kind": "body_chapter_start", "keep": true, "corrected_title": "Chapter II", "rationale": "real chapter start"}',
        )
    )

    monkeypatch.setattr(classifier, "_invoke_chat_completion", lambda prompt, config: next(responses))

    result = classifier.classify(book, config)

    assert [chunk.title for chunk in result.chunks] == ["Chapter I", "Chapter II"]
    assert result.chunks[0].order == 1


def test_llm_classifier_deduplicates_duplicate_chapter_suffix_by_longest_then_later() -> None:
    classifier = LLMEnhancedClassifier(layout_classifier=StubLayoutClassifier())

    longer = ChapterChunk(order=1, start_page=1, end_page=10, title="Chapter IX: Earlier Long")
    shorter = ChapterChunk(order=2, start_page=20, end_page=24, title="Chapter IX: Later Short")
    deduped, warnings = classifier._deduplicate_duplicate_suffixes([longer, shorter])

    assert len(deduped) == 1
    assert deduped[0].start_page == 1
    assert warnings

    first = ChapterChunk(order=1, start_page=30, end_page=34, title="Chapter X: Earlier")
    later = ChapterChunk(order=2, start_page=40, end_page=44, title="Chapter X: Later")
    deduped_tie, _ = classifier._deduplicate_duplicate_suffixes([first, later])

    assert len(deduped_tie) == 1
    assert deduped_tie[0].start_page == 40
