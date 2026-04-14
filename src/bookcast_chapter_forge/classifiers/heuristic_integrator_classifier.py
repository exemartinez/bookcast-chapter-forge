from __future__ import annotations

from collections import defaultdict

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.index_chapter_classifier import IndexChapterClassifier
from bookcast_chapter_forge.classifiers.layout_aware_classifier import LayoutAwareClassifier
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import RegexChapterClassifier
from bookcast_chapter_forge.classifiers.semantic_section_classifier import SemanticSectionClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, first_non_empty_line
from bookcast_chapter_forge.domain.entities import BoundaryCandidate, BookDocument, ClassificationResult, ParserConfig, SignalEvidence
from bookcast_chapter_forge.infrastructure.logging import EVENT_BOUNDARY_DECISION, EventLogger


class HeuristicIntegratorClassifier(ChapterClassifier):
    """Combine corroborated evidence from multiple strategies into one deterministic chapter plan."""

    def __init__(self, logger: EventLogger | None = None) -> None:
        """Bind a logger so integrator decisions can be inspected during real runs."""
        self._logger = logger or EventLogger()

    @property
    def strategy_name(self) -> str:
        return "heuristic"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        """Aggregate evidence from available strategies and choose stable boundary pages."""
        candidates, warnings = self._collect_candidates(book, config)
        if not candidates:
            raise ValueError("heuristic strategy could not identify corroborated boundary candidates")

        selected = self._select_candidates(candidates)
        starts = [(candidate.page, self._title_for_candidate(book, candidate)) for candidate in selected]
        chunks = build_chunks(starts, book.page_count)
        self._logger.progress(
            EVENT_BOUNDARY_DECISION,
            strategy=self.strategy_name,
            path=str(book.path),
            boundaries=[candidate.page for candidate in selected],
            warnings=len(warnings),
        )
        return ClassificationResult(
            chunks=chunks,
            warnings=tuple(warnings),
            metadata={"strategy": self.strategy_name, "signals": len(selected), "sources": len(candidates)},
        )

    def _collect_candidates(self, book: BookDocument, config: ParserConfig) -> tuple[list[BoundaryCandidate], list[str]]:
        """Run subordinate strategies, collect their start pages, and aggregate them into weighted candidates."""
        weighted_results: dict[int, list[SignalEvidence]] = defaultdict(list)
        warnings: list[str] = []

        for source, weight, classifier in self._strategy_sources(config):
            try:
                result = classifier.classify(book, config)
            except ValueError as exc:
                warnings.append(f"{source}: {exc}")
                continue
            except Exception as exc:
                warnings.append(f"{source}: runtime failure ({exc})")
                continue

            for chunk in result.chunks:
                label = chunk.title or first_non_empty_line(book.page_texts[chunk.start_page - 1]) or source.title()
                weighted_results[chunk.start_page].append(
                    SignalEvidence(source=source, page=chunk.start_page, label=label, score=weight)
                )

        candidates = [
            BoundaryCandidate(page=page, score=sum(signal.score for signal in signals), signals=tuple(signals))
            for page, signals in weighted_results.items()
        ]
        return candidates, warnings

    def _strategy_sources(self, config: ParserConfig) -> tuple[tuple[str, float, ChapterClassifier], ...]:
        """Define deterministic evidence source order and per-source weight."""
        sources: list[tuple[str, float, ChapterClassifier]] = [
            ("index", config.heuristic_signal_weights.get("index", 2.5), IndexChapterClassifier()),
            ("layout", config.heuristic_signal_weights.get("layout", 3.0), LayoutAwareClassifier()),
            ("semantic", config.heuristic_signal_weights.get("semantic", 2.0), SemanticSectionClassifier()),
            ("regex", config.heuristic_signal_weights.get("regex", 1.0), RegexChapterClassifier()),
        ]
        return tuple(sources)

    def _select_candidates(self, candidates: list[BoundaryCandidate]) -> list[BoundaryCandidate]:
        """Keep candidates with meaningful support and apply deterministic tie-break ordering."""
        accepted: list[BoundaryCandidate] = []
        for candidate in sorted(candidates, key=lambda item: (item.page, -item.score)):
            source_count = len({signal.source for signal in candidate.signals})
            if candidate.score <= 0 or source_count == 0:
                continue
            accepted.append(candidate)

        if not accepted:
            accepted = sorted(candidates, key=lambda item: (-item.score, item.page))[:1]

        return sorted(accepted, key=lambda item: item.page)

    def _title_for_candidate(self, book: BookDocument, candidate: BoundaryCandidate) -> str:
        """Prefer the strongest evidence label for a selected candidate page."""
        strongest = sorted(candidate.signals, key=lambda signal: (-signal.score, signal.source))[0]
        return strongest.label or first_non_empty_line(book.page_texts[candidate.page - 1]) or f"Page {candidate.page}"
