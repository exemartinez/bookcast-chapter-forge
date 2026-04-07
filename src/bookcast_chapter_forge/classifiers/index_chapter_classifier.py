from __future__ import annotations

import re

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import _first_non_empty_line, _normalize_title
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig


class IndexChapterClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "index"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        index_page_text = self._find_index_page_text(book, config)
        entries = self._parse_entries(index_page_text, config)
        if not entries:
            raise ValueError("No index entries could be parsed from the document")

        located_entries: list[tuple[str, int]] = []
        inferred_offset: int | None = None

        for title, printed_page in entries:
            actual_page = self._find_title_page(book, title)
            if actual_page is not None and inferred_offset is None:
                inferred_offset = actual_page - printed_page
            if actual_page is None and inferred_offset is not None:
                actual_page = printed_page + inferred_offset
            if actual_page is None:
                continue
            if 1 <= actual_page <= book.page_count:
                located_entries.append((title, actual_page))

        if len(located_entries) < 2:
            raise ValueError("No chapter starts could be located from the parsed index entries")

        deduped: list[tuple[str, int]] = []
        seen_pages: set[int] = set()
        for title, page in located_entries:
            if page not in seen_pages:
                deduped.append((title, page))
                seen_pages.add(page)

        chunks: list[ChapterChunk] = []
        for order, (title, page) in enumerate(deduped, start=1):
            next_page = deduped[order][1] if order < len(deduped) else book.page_count + 1
            chunks.append(ChapterChunk(order=order, start_page=page, end_page=next_page - 1, title=title))

        metadata: dict[str, str | int] = {"strategy": self.strategy_name}
        if inferred_offset is not None:
            metadata["page_offset"] = inferred_offset
        return ClassificationResult(chunks=tuple(chunks), metadata=metadata)

    def _find_index_page_text(self, book: BookDocument, config: ParserConfig) -> str:
        candidates = list(range(min(12, book.page_count))) + list(range(max(0, book.page_count - 12), book.page_count))
        for index in dict.fromkeys(candidates):
            text = book.page_texts[index]
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            head_lines = lines[:4]
            if any(re.search(pattern, line) for pattern in config.index_title_patterns for line in head_lines):
                return text
            if any("contents" in line.lower() or line.lower() == "index" for line in head_lines):
                return text
        raise ValueError("No valid index page was identified")

    def _parse_entries(self, text: str, config: ParserConfig) -> list[tuple[str, int]]:
        entries: list[tuple[str, int]] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            for pattern in config.index_entry_patterns:
                match = re.search(pattern, line)
                if match:
                    title = self._clean_title(match.group("title"))
                    page = int(match.group("page"))
                    if len(_normalize_title(title)) >= 3:
                        entries.append((title, page))
                        break
            else:
                fallback_page = re.search(r"(?P<page>\d+)\s*$", line)
                if fallback_page:
                    title = self._clean_title(line[: fallback_page.start()])
                    page = int(fallback_page.group("page"))
                    if len(_normalize_title(title)) >= 3:
                        entries.append((title, page))
        return entries

    def _clean_title(self, value: str) -> str:
        normalized = value.replace("\u00b7", ".")
        normalized = re.sub(r"(?:\s\.\s){2,}", "|", normalized)
        normalized = re.sub(r"[._-]{3,}", "|", normalized)
        segments = [re.sub(r"\s+", " ", part).strip(" .-_") for part in normalized.split("|")]
        segments = [segment for segment in segments if segment]
        if not segments:
            return ""
        return segments[0]

    def _find_title_page(self, book: BookDocument, title: str) -> int | None:
        normalized_title = _normalize_title(title)
        for page_number, text in enumerate(book.page_texts, start=1):
            first_line = _normalize_title(_first_non_empty_line(text))
            prefix = _normalize_title(" ".join(text.splitlines()[:4]))
            if first_line.startswith(normalized_title) or prefix.startswith(normalized_title):
                return page_number
            if normalized_title in prefix and len(normalized_title.split()) >= 3:
                return page_number
        return None
