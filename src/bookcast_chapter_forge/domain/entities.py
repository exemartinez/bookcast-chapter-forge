from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BookDocument:
    path: Path
    page_texts: tuple[str, ...]
    title: str | None = None

    @property
    def page_count(self) -> int:
        return len(self.page_texts)

    @property
    def stem(self) -> str:
        return self.path.stem


@dataclass(frozen=True)
class ChapterChunk:
    order: int
    start_page: int
    end_page: int
    title: str | None = None

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1


@dataclass(frozen=True)
class ParserConfig:
    max_pages_per_chunk: int
    regex_book_patterns: tuple[str, ...] = ()
    regex_english_patterns: tuple[str, ...] = ()
    regex_chapter_start_patterns: tuple[str, ...] = ()
    regex_chapter_end_patterns: tuple[str, ...] = ()
    regex_book_start_patterns: tuple[str, ...] = ()
    regex_book_end_patterns: tuple[str, ...] = ()
    index_title_patterns: tuple[str, ...] = ()
    index_entry_patterns: tuple[str, ...] = ()
    layout_heading_patterns: tuple[str, ...] = ()
    semantic_title_patterns: tuple[str, ...] = ()
    model_enabled: bool = False
    heuristic_signal_weights: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SignalEvidence:
    source: str
    page: int
    label: str
    score: float


@dataclass(frozen=True)
class BoundaryCandidate:
    page: int
    score: float
    signals: tuple[SignalEvidence, ...] = ()


@dataclass(frozen=True)
class BoundaryDecision:
    ordered_pages: tuple[int, ...]
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClassificationResult:
    chunks: tuple[ChapterChunk, ...]
    warnings: tuple[str, ...] = ()
    metadata: dict[str, str | int] = field(default_factory=dict)
