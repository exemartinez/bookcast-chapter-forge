from __future__ import annotations

import json
import re
from urllib import error, request

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.layout_aware_classifier import LayoutAwareClassifier
from bookcast_chapter_forge.domain.entities import (
    BookDocument,
    ChapterChunk,
    ClassificationResult,
    LLMReviewDecision,
    LLMReviewPacket,
    ParserConfig,
)
from bookcast_chapter_forge.infrastructure.logging import EVENT_LLM_REVIEW, EventLogger


class LLMEnhancedClassifier(ChapterClassifier):
    """Review layout-derived cuts with a local llama.cpp server before finalizing output chunks."""

    def __init__(
        self,
        layout_classifier: ChapterClassifier | None = None,
        logger: EventLogger | None = None,
    ) -> None:
        """Bind collaborators so the LLM reviewer stays layered on top of layout output."""
        self._layout_classifier = layout_classifier or LayoutAwareClassifier()
        self._logger = logger or EventLogger()

    @property
    def strategy_name(self) -> str:
        """Expose the user-facing strategy name."""
        return "llm"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        """Review each layout-derived chunk and keep only the LLM-approved cuts."""
        self._require_supported_provider(config)
        layout_result = self._layout_classifier.classify(book, config)
        chunks = list(layout_result.chunks)
        if not chunks:
            raise ValueError("llm strategy requires layout candidates but none were produced")

        reviewed_chunks: list[ChapterChunk] = []
        warnings = list(layout_result.warnings)
        for index, chunk in enumerate(chunks):
            packet = self._build_review_packet(book, chunks, index, config)
            try:
                decision = self._review_packet(packet, config)
            except ValueError as exc:
                if not self._is_unrecoverable_review_error(exc):
                    warnings.append(f"llm fallback on page {chunk.start_page}: {exc}")
                    decision = LLMReviewDecision(
                        keep=True,
                        corrected_title=chunk.title or packet.title,
                        rationale=f"fallback due to unparsable model output: {exc}",
                    )
                else:
                    raise
            self._logger.progress(
                EVENT_LLM_REVIEW,
                page=chunk.start_page,
                keep=decision.keep,
                corrected_title=decision.corrected_title,
            )
            if not decision.keep:
                warnings.append(f"llm rejected cut starting at page {chunk.start_page}: {decision.rationale}".strip())
                continue
            reviewed_chunks.append(
                ChapterChunk(
                    order=len(reviewed_chunks) + 1,
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                    title=decision.corrected_title or chunk.title,
                )
            )

        if not reviewed_chunks:
            raise ValueError("llm strategy rejected all layout-derived cuts")

        normalized_chunks = tuple(
            ChapterChunk(
                order=order,
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                title=chunk.title,
            )
            for order, chunk in enumerate(reviewed_chunks, start=1)
        )
        return ClassificationResult(
            chunks=normalized_chunks,
            warnings=tuple(warnings),
            metadata={
                "strategy": self.strategy_name,
                "provider": config.llm_provider,
                "model": config.llm_model,
                "reviewed_chunks": len(chunks),
                "kept_chunks": len(normalized_chunks),
            },
        )

    def _is_unrecoverable_review_error(self, exc: ValueError) -> bool:
        """Treat connectivity/runtime failures as fatal, but malformed answers as recoverable."""
        message = str(exc).lower()
        fatal_markers = ("reachable local llama-server runtime", "timed out while waiting for llama-server")
        return any(marker in message for marker in fatal_markers)

    def _require_supported_provider(self, config: ParserConfig) -> None:
        """Limit the MVP implementation to the provider defined in the spec."""
        if config.llm_provider.lower() != "llama.cpp":
            raise ValueError("llm strategy currently supports only provider=llama.cpp")

    def _build_review_packet(
        self,
        book: BookDocument,
        chunks: list[ChapterChunk],
        index: int,
        config: ParserConfig,
    ) -> LLMReviewPacket:
        """Build a bounded structured packet from the layout chunk and nearby context pages."""
        chunk = chunks[index]
        previous_title = chunks[index - 1].title or "" if index > 0 else ""
        next_title = chunks[index + 1].title or "" if index + 1 < len(chunks) else ""
        start_page = max(1, chunk.start_page - config.llm_review_window)
        end_page = min(book.page_count, chunk.end_page + config.llm_review_window)
        excerpts = [
            self._truncate_excerpt(book.page_texts[page_number - 1], config.llm_max_excerpt_chars)
            for page_number in range(start_page, end_page + 1)
        ]
        return LLMReviewPacket(
            title=chunk.title or f"Page {chunk.start_page}",
            proposed_start_page=chunk.start_page,
            proposed_end_page=chunk.end_page,
            previous_title=previous_title,
            next_title=next_title,
            context_excerpt="\n\n".join(excerpts),
        )

    def _truncate_excerpt(self, page_text: str, max_excerpt_chars: int) -> str:
        """Keep packet payloads small enough for local review requests."""
        text = " ".join(part.strip() for part in page_text.splitlines() if part.strip())
        return text[:max_excerpt_chars]

    def _review_packet(self, packet: LLMReviewPacket, config: ParserConfig) -> LLMReviewDecision:
        """Ask the local llama.cpp server whether to keep the cut and what title to use."""
        prompt = self._build_prompt(packet, config)
        raw_response = self._invoke_chat_completion(prompt, config)
        return self._parse_review_decision(raw_response, packet)

    def _build_prompt(self, packet: LLMReviewPacket, config: ParserConfig) -> str:
        """Render one strict JSON-only review request for the local model."""
        instructions = config.llm_prompt_instructions.strip()
        prompt_lines = [
            "You are reviewing a proposed chapter cut from a PDF.",
            "Return strict JSON with keys: keep, corrected_title, rationale.",
            "Do not use markdown fences, comments, or prose outside the JSON object.",
            "Use only the evidence provided. Do not invent missing pages.",
            "Prefer rejecting front matter, table of contents pages, and clearly mislabeled titles.",
            f"Proposed title: {packet.title}",
            f"Proposed page range: {packet.proposed_start_page}-{packet.proposed_end_page}",
            f"Previous title: {packet.previous_title or '(none)'}",
            f"Next title: {packet.next_title or '(none)'}",
            f"Context:\n{packet.context_excerpt}",
        ]
        if instructions:
            prompt_lines.append(f"Additional instructions: {instructions}")
        return "\n".join(prompt_lines)

    def _invoke_chat_completion(self, prompt: str, config: ParserConfig) -> str:
        """Call the local OpenAI-compatible chat completion endpoint exposed by llama-server."""
        payload = json.dumps(
            {
                "model": config.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
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
            raise ValueError("llm strategy requires a reachable local llama-server runtime") from exc
        except TimeoutError as exc:
            raise ValueError("llm strategy timed out while waiting for llama-server") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ValueError("llm strategy received a non-JSON response from llama-server") from exc
        try:
            return str(parsed["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("llm strategy received an unexpected chat completion payload") from exc

    def _parse_review_decision(self, raw_response: str, packet: LLMReviewPacket) -> LLMReviewDecision:
        """Parse the model's JSON response into a typed review decision."""
        cleaned_response = self._extract_json_object(raw_response)
        try:
            parsed = json.loads(cleaned_response)
        except json.JSONDecodeError as exc:
            raise ValueError("llm strategy received invalid JSON from the local model") from exc
        return LLMReviewDecision(
            keep=bool(parsed.get("keep", False)),
            corrected_title=str(parsed.get("corrected_title", packet.title)).strip() or packet.title,
            rationale=str(parsed.get("rationale", "")).strip(),
        )

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
