from __future__ import annotations

import re

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, first_non_empty_line
from bookcast_chapter_forge.domain.entities import BoundaryCandidate, BookDocument, ClassificationResult, ParserConfig, SignalEvidence


class ModelAssistedClassifier(ChapterClassifier):
    """Rank structured boundary candidates for optional local-model-assisted chapter selection."""

    @property
    def strategy_name(self) -> str:
        return "model"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        """Rank structured candidates and convert the selected pages into standard chunks."""
        if not config.model_enabled:
            raise ValueError("model strategy is disabled; set model.enabled=true in config")
        self._require_optional_dependency()

        patterns = config.semantic_title_patterns or config.regex_chapter_start_patterns
        if not patterns:
            raise ValueError("model strategy requires structured candidate patterns")

        candidates = self._build_candidates(book, patterns)
        if not candidates:
            raise ValueError("model strategy could not build structured boundary candidates")

        selected = self._rank_candidates(candidates)
        starts = [(candidate.page, self._title_for_candidate(book, candidate.page)) for candidate in selected]
        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(
            chunks=chunks,
            warnings=("model runtime integration is not configured; deterministic structured ranking used",),
            metadata={"strategy": self.strategy_name, "evidence": "structured-candidates", "signals": len(selected)},
        )

    def _require_optional_dependency(self) -> None:
        """Fail cleanly when LangChain is unavailable for the model-assisted mode."""
        try:
            __import__("langchain")
        except ModuleNotFoundError as exc:
            raise ValueError("model strategy requires optional dependency: langchain") from exc

    def _build_candidates(self, book: BookDocument, patterns: tuple[str, ...]) -> list[BoundaryCandidate]:
        """Construct candidates from heading-like first lines instead of sending raw full text to a model."""
        candidates: list[BoundaryCandidate] = []
        for page_number, page_text in enumerate(book.page_texts, start=1):
            first_line = first_non_empty_line(page_text)
            if not first_line:
                continue
            if not any(re.search(pattern, first_line) for pattern in patterns):
                continue
            evidence = SignalEvidence(source="first-line-pattern", page=page_number, label=first_line, score=1.0)
            candidates.append(BoundaryCandidate(page=page_number, score=1.0, signals=(evidence,)))
        return candidates

    def _rank_candidates(self, candidates: list[BoundaryCandidate]) -> list[BoundaryCandidate]:
        """Apply deterministic ranking over structured candidates until a local runtime is added."""
        ranked = sorted(candidates, key=lambda candidate: (-candidate.score, candidate.page))
        deduped: list[BoundaryCandidate] = []
        seen_pages: set[int] = set()
        for candidate in ranked:
            if candidate.page in seen_pages:
                continue
            deduped.append(candidate)
            seen_pages.add(candidate.page)
        return sorted(deduped, key=lambda candidate: candidate.page)

    def _title_for_candidate(self, book: BookDocument, page: int) -> str:
        """Use the candidate page's first non-empty line as the chunk title."""
        return first_non_empty_line(book.page_texts[page - 1]) or f"Page {page}"
