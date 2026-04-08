from __future__ import annotations

import re

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def _normalize_title(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _is_sparse_heading_page(text: str, first_line: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not first_line or not lines:
        return False
    words = first_line.split()
    if len(words) > 10 or len(first_line) > 90:
        return False
    if first_line.endswith((".", "!", "?", ";")):
        return False
    title_case_words = sum(1 for word in words if word[:1].isupper() or word.isupper())
    title_case_ratio = title_case_words / max(len(words), 1)
    return len(lines) <= 6 and title_case_ratio >= 0.6


class RegexChapterClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "regex"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        if book.page_count == 0:
            raise ValueError("The PDF has no pages")
        if not self._looks_english(book, config):
            raise ValueError("The PDF does not appear to be English")

        starts: list[tuple[int, str]] = []
        last_title = ""
        repeated_heading_titles = self._infer_repeated_heading_titles(book)

        for page_number, text in enumerate(book.page_texts, start=1):
            first_line = _first_non_empty_line(text)
            page_prefix = "\n".join(text.splitlines()[:4]).strip()
            if self._matches_start(first_line, page_prefix, text, repeated_heading_titles, config):
                title = first_line or f"Chapter {page_number}"
                normalized = _normalize_title(title)
                if normalized and normalized != last_title:
                    starts.append((page_number, title))
                    last_title = normalized

        if not starts:
            raise ValueError("No chapter boundaries were identified by regex strategy")
        if len(starts) < 2 and book.page_count > max(10, config.max_pages_per_chunk):
            raise ValueError("The PDF does not appear to contain reliable generic chapter boundaries")

        chunks: list[ChapterChunk] = []
        for order, (page_number, title) in enumerate(starts, start=1):
            next_start = starts[order][0] if order < len(starts) else book.page_count + 1
            chunks.append(
                ChapterChunk(
                    order=order,
                    start_page=page_number,
                    end_page=next_start - 1,
                    title=title,
                )
            )
        return ClassificationResult(chunks=tuple(chunks), metadata={"strategy": self.strategy_name})

    def _looks_english(self, book: BookDocument, config: ParserConfig) -> bool:
        if not config.regex_english_patterns:
            return True
        sample = " ".join(book.page_texts[: min(20, book.page_count)])
        return any(re.search(pattern, sample) for pattern in config.regex_english_patterns)

    def _matches_start(
        self,
        first_line: str,
        page_prefix: str,
        page_text: str,
        repeated_heading_titles: set[str],
        config: ParserConfig,
    ) -> bool:
        patterns = list(config.regex_chapter_start_patterns) + list(config.regex_book_start_patterns)
        if any(re.search(pattern, first_line) for pattern in patterns if first_line):
            return True
        if _is_sparse_heading_page(page_text, first_line) and any(re.search(pattern, page_prefix) for pattern in patterns if page_prefix):
            return True

        normalized = _normalize_title(first_line)
        return normalized in repeated_heading_titles and _is_sparse_heading_page(page_text, first_line)

    def _infer_repeated_heading_titles(self, book: BookDocument) -> set[str]:
        counts: dict[str, int] = {}
        for text in book.page_texts:
            first_line = _first_non_empty_line(text)
            normalized = _normalize_title(first_line)
            if len(normalized.split()) < 2:
                continue
            if _is_sparse_heading_page(text, first_line):
                counts[normalized] = counts.get(normalized, 0) + 1
        return {title for title, count in counts.items() if count >= 1}
