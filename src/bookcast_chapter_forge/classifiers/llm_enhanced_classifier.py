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

    NON_BODY_PAGE_KINDS = {"toc", "chapter_summary", "front_matter", "other"}

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
        """Review each layout-derived chunk and keep only body-chapter starts."""
        self._require_supported_provider(config)
        layout_result = self._layout_classifier.classify(book, config)
        chunks = list(layout_result.chunks)
        if not chunks:
            raise ValueError("llm strategy requires layout candidates but none were produced")

        reviewed_chunks: list[ChapterChunk] = []
        warnings = list(layout_result.warnings)
        seen_titles: set[str] = set()
        for index, chunk in enumerate(chunks):
            if self._needs_review(chunk, index, chunks, seen_titles):
                packet = self._build_review_packet(book, chunks, index, config)
                try:
                    decision = self._review_packet(packet, config)
                except ValueError as exc:
                    if not self._is_unrecoverable_review_error(exc):
                        warnings.append(f"llm fallback on page {chunk.start_page}: {exc}")
                        decision = LLMReviewDecision(
                            page_kind="body_chapter_start",
                            keep=True,
                            corrected_title=chunk.title or packet.title,
                            rationale=f"fallback due to unparsable model output: {exc}",
                        )
                    else:
                        raise
            else:
                decision = LLMReviewDecision(
                    page_kind="body_chapter_start",
                    keep=True,
                    corrected_title=chunk.title or f"Page {chunk.start_page}",
                    rationale="skipped llm review for non-suspicious layout cut",
                )
            self._logger.progress(
                EVENT_LLM_REVIEW,
                page=chunk.start_page,
                page_kind=decision.page_kind,
                keep=decision.keep,
                corrected_title=decision.corrected_title,
            )
            if not decision.keep or decision.page_kind in self.NON_BODY_PAGE_KINDS:
                warnings.append(f"llm rejected cut starting at page {chunk.start_page}: {decision.rationale}".strip())
                continue
            seen_titles.add(self._normalize_title(decision.corrected_title or chunk.title or ""))
            reviewed_chunks.append(
                ChapterChunk(
                    order=len(reviewed_chunks) + 1,
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                    title=decision.corrected_title or chunk.title,
                )
            )

        reviewed_chunks = self._discard_leading_non_body_chunks(reviewed_chunks)
        reviewed_chunks, dedupe_warnings = self._deduplicate_duplicate_suffixes(reviewed_chunks)
        warnings.extend(dedupe_warnings)

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

    def _discard_leading_non_body_chunks(self, chunks: list[ChapterChunk]) -> list[ChapterChunk]:
        """Normalize final output to begin at the first accepted body chapter."""
        if not chunks:
            return chunks
        return [
            ChapterChunk(
                order=order,
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                title=chunk.title,
            )
            for order, chunk in enumerate(chunks, start=1)
        ]

    def _deduplicate_duplicate_suffixes(self, chunks: list[ChapterChunk]) -> tuple[list[ChapterChunk], list[str]]:
        """Keep only the strongest chunk when multiple outputs collapse to the same chapter suffix."""
        if not chunks:
            return [], []

        selected_by_suffix: dict[str, ChapterChunk] = {}
        warnings: list[str] = []
        for chunk in chunks:
            suffix = self._normalized_suffix(chunk)
            existing = selected_by_suffix.get(suffix)
            if existing is None:
                selected_by_suffix[suffix] = chunk
                continue
            winner, loser = self._choose_duplicate_winner(existing, chunk)
            selected_by_suffix[suffix] = winner
            warnings.append(
                f"llm deduplicated suffix {suffix}: kept pages {winner.start_page}-{winner.end_page}, "
                f"dropped pages {loser.start_page}-{loser.end_page}"
            )

        deduplicated = sorted(selected_by_suffix.values(), key=lambda chunk: chunk.start_page)
        return [
            ChapterChunk(
                order=order,
                start_page=chunk.start_page,
                end_page=chunk.end_page,
                title=chunk.title,
            )
            for order, chunk in enumerate(deduplicated, start=1)
        ], warnings

    def _choose_duplicate_winner(self, existing: ChapterChunk, candidate: ChapterChunk) -> tuple[ChapterChunk, ChapterChunk]:
        """Prefer the longer chunk; on ties prefer the later one."""
        existing_pages = existing.page_count
        candidate_pages = candidate.page_count
        if candidate_pages > existing_pages:
            return candidate, existing
        if candidate_pages < existing_pages:
            return existing, candidate
        if candidate.start_page >= existing.start_page:
            return candidate, existing
        return existing, candidate

    def _normalized_suffix(self, chunk: ChapterChunk) -> str:
        """Match the output writer's title suffix rules so duplicates are detected before writing."""
        title = self._sanitize_filename(chunk.title or f"Page {chunk.start_page}")
        parts = title.split("-")
        if len(parts) >= 2 and parts[0].lower() in {"chapter", "part", "section", "book"}:
            return "-".join(parts[:2])[:20].rstrip("-")
        return title[:20].rstrip("-")

    def _sanitize_filename(self, value: str) -> str:
        """Normalize title text into the same slug family used for output filenames."""
        normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip())
        normalized = re.sub(r"-+", "-", normalized).strip("-")
        return normalized or "chunk"

    def _is_unrecoverable_review_error(self, exc: ValueError) -> bool:
        """Treat connectivity/runtime failures as fatal, but malformed answers as recoverable."""
        message = str(exc).lower()
        fatal_markers = ("reachable local llama-server runtime", "timed out while waiting for llama-server")
        return any(marker in message for marker in fatal_markers)

    def _require_supported_provider(self, config: ParserConfig) -> None:
        """Limit the MVP implementation to the provider defined in the spec."""
        if config.llm_provider.lower() != "llama.cpp":
            raise ValueError("llm strategy currently supports only provider=llama.cpp")

    def _needs_review(
        self,
        chunk: ChapterChunk,
        index: int,
        chunks: list[ChapterChunk],
        seen_titles: set[str],
    ) -> bool:
        """Review only suspicious cuts so local inference remains practical."""
        title = (chunk.title or "").strip()
        normalized = self._normalize_title(title)
        if index < 2:
            return True
        if chunk.start_page <= 25:
            return True
        if len(title.split()) > 12 or len(title) > 100:
            return True
        if normalized in seen_titles:
            return True
        if any(marker in normalized for marker in ("contents", "table of contents", "preface", "foreword", "acknowledg")):
            return True
        previous_chunk = chunks[index - 1]
        if chunk.start_page - previous_chunk.start_page <= 2:
            return True
        return False

    def _normalize_title(self, title: str) -> str:
        """Normalize titles for duplicate and front-matter heuristics."""
        return re.sub(r"\s+", " ", title.strip().lower())

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
        lines = [part.strip() for part in page_text.splitlines() if part.strip()]
        text = " ".join(lines[:5])
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
            "Return strict JSON with keys: page_kind, keep, corrected_title, rationale.",
            "Do not use markdown fences, comments, or prose outside the JSON object.",
            "Use only the evidence provided. Do not invent missing pages.",
            "Classify page_kind as one of: body_chapter_start, toc, chapter_summary, front_matter, other.",
            "Only use body_chapter_start when this page is the true first page of chapter body content.",
            "Reject TOC pages, chapter-summary spreads, front matter, and other non-body material even if they show large chapter headings.",
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
                "max_tokens": 80,
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
        page_kind = str(parsed.get("page_kind", "")).strip().lower() or "other"
        keep = bool(parsed.get("keep", False))
        if page_kind in self.NON_BODY_PAGE_KINDS:
            keep = False
        return LLMReviewDecision(
            page_kind=page_kind,
            keep=keep,
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
