from __future__ import annotations

from pathlib import Path

import pytest

from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig
from bookcast_chapter_forge.services.adaptive_parser_wrapper import AdaptiveParserWrapper
from bookcast_chapter_forge.services.output_writer import OutputWriter


def _book(page_count: int = 20) -> BookDocument:
    return BookDocument(path=Path("book.pdf"), page_texts=tuple(f"Page {index}" for index in range(1, page_count + 1)))


def _config(**overrides) -> ParserConfig:
    base = ParserConfig(max_pages_per_chunk=10)
    values = {field: getattr(base, field) for field in base.__dataclass_fields__}
    values.update(overrides)
    return ParserConfig(**values)


def test_adaptive_wrapper_stops_on_first_accepted_result() -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))
    calls: list[str] = []

    def classify_with_strategy(strategy: str) -> ClassificationResult:
        calls.append(strategy)
        return ClassificationResult(chunks=(ChapterChunk(order=1, start_page=1, end_page=5, title="Chapter I"),))

    strategy, result, decision = wrapper.select_result(
        _book(),
        _config(adaptive_min_output_files=1),
        classify_with_strategy=classify_with_strategy,
        validate_result=lambda book, strategy, result: None,
    )

    assert strategy == "regex"
    assert len(result.chunks) == 1
    assert decision.selected_strategy == "regex"
    assert calls == ["regex"]


def test_adaptive_wrapper_continues_after_failure_until_later_strategy_succeeds() -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))
    calls: list[str] = []

    def classify_with_strategy(strategy: str) -> ClassificationResult:
        calls.append(strategy)
        if strategy == "regex":
            raise ValueError("regex failed")
        return ClassificationResult(chunks=(ChapterChunk(order=1, start_page=2, end_page=6, title="Chapter I"),))

    strategy, _, decision = wrapper.select_result(
        _book(),
        _config(adaptive_min_output_files=1),
        classify_with_strategy=classify_with_strategy,
        validate_result=lambda book, strategy, result: None,
    )

    assert strategy == "layout"
    assert [attempt.status for attempt in decision.attempts] == ["failed", "accepted"]
    assert calls == ["regex", "layout"]


def test_adaptive_wrapper_rejects_duplicate_output_suffixes() -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))
    result = ClassificationResult(
        chunks=(
            ChapterChunk(order=1, start_page=1, end_page=5, title="Chapter IX"),
            ChapterChunk(order=2, start_page=6, end_page=10, title="Chapter IX"),
        )
    )

    review = wrapper._review_result(_book(), "regex", result, _config(adaptive_min_output_files=1))

    assert review.accepted is False
    assert "not unique" in review.rationale


def test_adaptive_wrapper_rejects_invalid_page_spans() -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))
    result = ClassificationResult(chunks=(ChapterChunk(order=1, start_page=1, end_page=30, title="Chapter I"),))

    review = wrapper._review_result(_book(page_count=10), "layout", result, _config(adaptive_min_output_files=1))

    assert review.accepted is False
    assert "invalid relative to source page count" in review.rationale


def test_adaptive_wrapper_uses_llm_mind_for_low_file_count(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))
    result = ClassificationResult(chunks=(ChapterChunk(order=1, start_page=1, end_page=5, title="Chapter I"),))
    monkeypatch.setattr(
        wrapper,
        "_invoke_chat_completion",
        lambda prompt, config: '{"accept": true, "rationale": "single output still sensible"}',
    )

    review = wrapper._review_result(_book(), "layout", result, _config(adaptive_min_output_files=3))

    assert review.accepted is True
    assert review.review_source == "llm_mind"


def test_adaptive_wrapper_continues_when_llm_mind_rejects_result(monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))
    calls: list[str] = []

    def classify_with_strategy(strategy: str) -> ClassificationResult:
        calls.append(strategy)
        if strategy == "regex":
            return ClassificationResult(chunks=(ChapterChunk(order=1, start_page=1, end_page=5, title="Chapter I"),))
        return ClassificationResult(chunks=(ChapterChunk(order=1, start_page=10, end_page=15, title="Chapter II"),))

    responses = iter(
        (
            '{"accept": false, "rationale": "single output looks suspicious"}',
            '{"accept": true, "rationale": "later output looks sensible"}',
        )
    )
    monkeypatch.setattr(wrapper, "_invoke_chat_completion", lambda prompt, config: next(responses))

    strategy, _, decision = wrapper.select_result(
        _book(),
        _config(adaptive_min_output_files=3),
        classify_with_strategy=classify_with_strategy,
        validate_result=lambda book, strategy, result: None,
    )

    assert strategy == "layout"
    assert [attempt.status for attempt in decision.attempts] == ["rejected", "accepted"]
    assert calls == ["regex", "layout"]


def test_adaptive_wrapper_reports_attempt_path_metadata() -> None:
    wrapper = AdaptiveParserWrapper(output_writer=OutputWriter(output_dir="output"))

    strategy, result, decision = wrapper.select_result(
        _book(),
        _config(adaptive_min_output_files=1),
        classify_with_strategy=lambda strategy: ClassificationResult(chunks=(ChapterChunk(order=1, start_page=1, end_page=4, title="Chapter I"),)),
        validate_result=lambda book, strategy, result: None,
    )

    assert strategy == "regex"
    assert result.metadata["adaptive_selected_strategy"] == "regex"
    assert result.metadata["adaptive_attempt_count"] == 1
    assert decision.review.review_source == "deterministic"
