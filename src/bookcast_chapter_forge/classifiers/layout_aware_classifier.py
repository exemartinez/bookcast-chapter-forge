from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.utils import build_chunks, first_non_empty_line
from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig


@dataclass(frozen=True)
class _FontFragment:
    """Represents one extracted text fragment with its rendered font size."""

    text: str
    font_size: float
    order: int


class LayoutAwareClassifier(ChapterClassifier):
    """Infer chapter starts from page-local heading typography rather than plain text alone."""

    @property
    def strategy_name(self) -> str:
        return "layout"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        """Build chunks from pages whose dominant heading-like text matches configured patterns."""
        self._require_optional_dependency()

        patterns = config.layout_heading_patterns or config.regex_chapter_start_patterns
        if not patterns:
            raise ValueError("layout strategy requires heading patterns")

        starts = self._extract_layout_starts(book, patterns)
        if not starts:
            raise ValueError("layout strategy could not identify layout-aware chapter starts")

        chunks = build_chunks(starts, book.page_count)
        return ClassificationResult(
            chunks=chunks,
            metadata={"strategy": self.strategy_name, "evidence": "page-typography", "signals": len(starts)},
        )

    def _require_optional_dependency(self) -> None:
        """Fail cleanly when the optional layout stack is not installed."""
        try:
            __import__("pymupdf4llm")
        except ModuleNotFoundError as exc:
            raise ValueError("layout strategy requires optional dependency: pymupdf4llm") from exc

    def _extract_layout_starts(self, book: BookDocument, patterns: tuple[str, ...]) -> list[tuple[int, str]]:
        """Detect chapter starts from the largest-font text fragments on each page."""
        reader = self._open_reader(book.path)
        starts: list[tuple[int, str]] = []

        for page_number in range(1, book.page_count + 1):
            fragments = self._extract_fragments(reader, page_number) if reader else ()
            candidates = self._candidate_heading_texts(book.page_texts[page_number - 1], fragments)
            for candidate in candidates:
                if candidate and any(re.search(pattern, candidate) for pattern in patterns):
                    starts.append((page_number, candidate))
                    break

        return starts

    def _open_reader(self, path: Path) -> PdfReader | None:
        """Open the backing PDF when available, otherwise fall back to text-only unit-test mode."""
        if not path.exists():
            return None
        try:
            return PdfReader(str(path))
        except Exception:
            return None

    def _extract_fragments(self, reader: PdfReader, page_number: int) -> tuple[_FontFragment, ...]:
        """Collect visible text fragments with font sizes from one page."""
        fragments: list[_FontFragment] = []
        order = 0

        def visitor(text, _cm, _tm, _font_dict, font_size):
            nonlocal order
            if text and text.strip():
                fragments.append(_FontFragment(text=text.strip(), font_size=float(font_size or 0), order=order))
                order += 1

        try:
            reader.pages[page_number - 1].extract_text(visitor_text=visitor)
        except Exception:
            return ()

        return tuple(fragments)

    def _candidate_heading_texts(self, page_text: str, fragments: tuple[_FontFragment, ...]) -> tuple[str, ...]:
        """Prioritize the largest-font text, then fall back to the page's first non-empty line."""
        if not fragments:
            first_line = first_non_empty_line(page_text)
            return (first_line,) if first_line else ()

        grouped: dict[float, list[str]] = {}
        for fragment in fragments:
            grouped.setdefault(round(fragment.font_size, 2), []).append(fragment.text)

        candidates: list[str] = []
        for font_size in sorted(grouped, reverse=True)[:3]:
            text = " ".join(grouped[font_size]).strip()
            if text:
                candidates.append(text)

        first_line = first_non_empty_line(page_text)
        if first_line and first_line not in candidates:
            candidates.append(first_line)
        return tuple(candidates)
