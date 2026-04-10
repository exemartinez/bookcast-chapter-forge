from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BookDocument:
    """Represents one parsed book and the page text extracted from it."""

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
    """Represents one contiguous output chunk in the source PDF."""

    order: int
    start_page: int
    end_page: int
    title: str | None = None

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1


@dataclass(frozen=True)
class ParserConfig:
    """Holds normalized parser settings loaded from the YAML config file."""

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
    llm_provider: str = "llama.cpp"
    llm_model: str = "ggml-org/gemma-3-1b-it-GGUF"
    llm_base_url: str = "http://127.0.0.1:8080"
    llm_timeout_seconds: float = 30.0
    llm_review_window: int = 1
    llm_max_excerpt_chars: int = 300
    llm_prompt_instructions: str = ""


@dataclass(frozen=True)
class SignalEvidence:
    """Captures one strategy-specific signal supporting a boundary candidate."""

    source: str
    page: int
    label: str
    score: float


@dataclass(frozen=True)
class BoundaryCandidate:
    """Represents one possible boundary page and the signals supporting it."""

    page: int
    score: float
    signals: tuple[SignalEvidence, ...] = ()


@dataclass(frozen=True)
class BoundaryDecision:
    """Represents the final ordered boundary selection after scoring."""

    ordered_pages: tuple[int, ...]
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class LLMReviewPacket:
    """Carries local evidence for one layout-derived cut into the LLM review step."""

    title: str
    proposed_start_page: int
    proposed_end_page: int
    previous_title: str
    next_title: str
    context_excerpt: str


@dataclass(frozen=True)
class LLMReviewDecision:
    """Carries the LLM reviewer decision for one proposed chunk."""

    page_kind: str
    keep: bool
    corrected_title: str
    rationale: str = ""


@dataclass(frozen=True)
class ClassificationResult:
    """Represents the classifier output and any diagnostics emitted during it."""

    chunks: tuple[ChapterChunk, ...]
    warnings: tuple[str, ...] = ()
    metadata: dict[str, str | int] = field(default_factory=dict)
