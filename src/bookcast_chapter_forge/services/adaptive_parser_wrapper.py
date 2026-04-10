from __future__ import annotations

import json
import re
from typing import Callable
from urllib import error, request

from bookcast_chapter_forge.domain.entities import (
    AdaptiveDecision,
    BookDocument,
    ClassificationResult,
    OutputSensibilityReview,
    ParserConfig,
    StrategyAttempt,
)
from bookcast_chapter_forge.infrastructure.logging import (
    EVENT_ADAPTIVE_ATTEMPT,
    EVENT_ADAPTIVE_REVIEW,
    EVENT_ADAPTIVE_WINNER,
    EventLogger,
)
from bookcast_chapter_forge.services.output_writer import OutputWriter


class AdaptiveParserWrapper:
    """Orchestrate parser strategy execution and stop at the first sensible result."""

    def __init__(self, output_writer: OutputWriter, logger: EventLogger | None = None) -> None:
        """Bind collaborators used for filename simulation and structured diagnostics."""
        self._output_writer = output_writer
        self._logger = logger or EventLogger()

    def select_result(
        self,
        book: BookDocument,
        config: ParserConfig,
        classify_with_strategy: Callable[[str], ClassificationResult],
        validate_result: Callable[[BookDocument, str, ClassificationResult], None],
    ) -> tuple[str, ClassificationResult, AdaptiveDecision]:
        """Run the fallback cascade and return the first accepted classification result."""
        attempts: list[StrategyAttempt] = []
        rejection_warnings: list[str] = []
        for strategy in config.adaptive_fallback_order:
            try:
                result = classify_with_strategy(strategy)
                validate_result(book, strategy, result)
            except Exception as exc:
                reason = str(exc)
                attempts.append(StrategyAttempt(strategy=strategy, status="failed", reason=reason))
                self._logger.warning(EVENT_ADAPTIVE_ATTEMPT, strategy=strategy, status="failed", reason=reason)
                rejection_warnings.append(f"adaptive {strategy} failed: {reason}")
                continue

            review = self._review_result(book, strategy, result, config)
            status = "accepted" if review.accepted else "rejected"
            attempts.append(StrategyAttempt(strategy=strategy, status=status, reason=review.rationale))
            self._logger.progress(
                EVENT_ADAPTIVE_REVIEW,
                strategy=strategy,
                accepted=review.accepted,
                source=review.review_source,
                rationale=review.rationale,
            )
            if review.accepted:
                metadata = dict(result.metadata)
                metadata.update(
                    {
                        "adaptive_selected_strategy": strategy,
                        "adaptive_attempt_count": len(attempts),
                        "adaptive_review_source": review.review_source,
                    }
                )
                attempt_path = " -> ".join(f"{attempt.strategy}:{attempt.status}" for attempt in attempts)
                warnings = tuple(rejection_warnings) + result.warnings
                decision = AdaptiveDecision(
                    attempts=tuple(attempts),
                    selected_strategy=strategy,
                    review=review,
                )
                self._logger.info(
                    EVENT_ADAPTIVE_WINNER,
                    strategy=strategy,
                    attempts=len(attempts),
                    attempt_path=attempt_path,
                )
                return strategy, ClassificationResult(chunks=result.chunks, warnings=warnings, metadata=metadata), decision

            rejection_warnings.append(f"adaptive {strategy} rejected: {review.rationale}")

        failure_reason = "; ".join(f"{attempt.strategy}:{attempt.reason}" for attempt in attempts) or "no strategies attempted"
        raise ValueError(f"adaptive wrapper could not produce a sensible result: {failure_reason}")

    def _review_result(
        self,
        book: BookDocument,
        strategy: str,
        result: ClassificationResult,
        config: ParserConfig,
    ) -> OutputSensibilityReview:
        """Apply deterministic sanity checks, then bounded low-file-count LLM review if needed."""
        filenames = self._simulate_output_filenames(book, result)
        deterministic_failure = self._deterministic_rejection_reason(book, result, filenames)
        if deterministic_failure:
            return OutputSensibilityReview(accepted=False, rationale=deterministic_failure, review_source="deterministic")
        if len(result.chunks) >= config.adaptive_min_output_files:
            return OutputSensibilityReview(
                accepted=True,
                rationale="deterministic checks passed and output count is sufficient",
                review_source="deterministic",
            )
        return self._invoke_llm_mind(book, strategy, result, filenames, config)

    def _simulate_output_filenames(self, book: BookDocument, result: ClassificationResult) -> tuple[str, ...]:
        """Generate would-be output filenames without writing files to disk."""
        return tuple(
            self._output_writer.filename_for_chunk(book, chunk)
            for chunk in result.chunks
        )

    def _deterministic_rejection_reason(
        self,
        book: BookDocument,
        result: ClassificationResult,
        filenames: tuple[str, ...],
    ) -> str | None:
        """Reject obviously invalid outputs before involving the local model."""
        for chunk in result.chunks:
            if chunk.start_page < 1 or chunk.end_page > book.page_count or chunk.page_count > book.page_count:
                return f"chunk {chunk.start_page}-{chunk.end_page} is invalid relative to source page count {book.page_count}"
        suffixes = [self.normalized_output_suffix(name) for name in filenames]
        if len(set(suffixes)) != len(suffixes):
            return "output filenames are not unique after removing the numeric sequence prefix"
        return None

    def normalized_output_suffix(self, filename: str) -> str:
        """Normalize an output filename by removing the book stem and numeric sequence prefix."""
        stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
        match = re.match(r"^.+?-\d{3}-(.+)$", stem)
        if match:
            return match.group(1)
        return stem

    def _invoke_llm_mind(
        self,
        book: BookDocument,
        strategy: str,
        result: ClassificationResult,
        filenames: tuple[str, ...],
        config: ParserConfig,
    ) -> OutputSensibilityReview:
        """Ask the local model whether a low-file-count result looks sensible enough to keep."""
        prompt = self._build_review_prompt(book, strategy, result, filenames, config)
        raw_response = self._invoke_chat_completion(prompt, config)
        parsed = self._parse_review_response(raw_response)
        return OutputSensibilityReview(
            accepted=bool(parsed.get("accept", False)),
            rationale=str(parsed.get("rationale", "")).strip() or "llm review returned no rationale",
            review_source="llm_mind",
        )

    def _build_review_prompt(
        self,
        book: BookDocument,
        strategy: str,
        result: ClassificationResult,
        filenames: tuple[str, ...],
        config: ParserConfig,
    ) -> str:
        """Render a bounded sensibility-review request over produced outputs only."""
        chunk_lines = [
            f"- {filename}: pages {chunk.start_page}-{chunk.end_page} title={chunk.title or '(none)'}"
            for filename, chunk in zip(filenames, result.chunks, strict=False)
        ]
        prompt_lines = [
            "You are reviewing a candidate PDF chunking result.",
            "Return strict JSON only with keys: accept, rationale.",
            "Decide whether the produced output files look sensible enough to stop fallback.",
            "Reject suspicious results, especially if the book appears to have been chunked incorrectly.",
            f"Source page count: {book.page_count}",
            f"Strategy: {strategy}",
            f"Produced file count: {len(result.chunks)}",
            "Produced files:",
            *chunk_lines,
        ]
        if config.adaptive_prompt_instructions.strip():
            prompt_lines.append(f"Additional instructions: {config.adaptive_prompt_instructions.strip()}")
        return "\n".join(prompt_lines)

    def _invoke_chat_completion(self, prompt: str, config: ParserConfig) -> str:
        """Call the local OpenAI-compatible chat completion endpoint exposed by llama-server."""
        payload = json.dumps(
            {
                "model": config.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 120,
            }
        ).encode("utf-8")
        endpoint = f"{config.llm_base_url.rstrip('/')}/v1/chat/completions"
        http_request = request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=config.llm_timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.URLError as exc:
            raise ValueError("adaptive wrapper requires a reachable local llama-server runtime") from exc
        except TimeoutError as exc:
            raise ValueError("adaptive wrapper timed out while waiting for llama-server") from exc

        try:
            parsed = json.loads(body)
            return str(parsed["choices"][0]["message"]["content"]).strip()
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ValueError("adaptive wrapper received an invalid response from llama-server") from exc

    def _parse_review_response(self, raw_response: str) -> dict[str, object]:
        """Recover the JSON review object from plain or fenced model output."""
        cleaned = self._extract_json_object(raw_response)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError("adaptive wrapper received invalid JSON from the local model") from exc

    def _extract_json_object(self, raw_response: str) -> str:
        """Recover the first JSON object from markdown-fenced or mixed model output."""
        stripped = raw_response.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
        if fenced_match:
            return fenced_match.group(1)
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return stripped
