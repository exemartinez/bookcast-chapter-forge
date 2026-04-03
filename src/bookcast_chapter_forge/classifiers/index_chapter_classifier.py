from __future__ import annotations

import re

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import KNOWN_BOOK_TITLES, _first_non_empty_line, _normalize_title
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig

CANONICAL_BOOK_TITLES = {title: title.title() for title in KNOWN_BOOK_TITLES}
CANONICAL_BOOK_TITLES["song of songs"] = "Song of Songs"


class IndexChapterClassifier(ChapterClassifier):
    def __init__(self) -> None:
        self._regex_classifier = None

    @property
    def strategy_name(self) -> str:
        return "index"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        index_page_text = self._find_index_page_text(book, config)
        entries = self._parse_entries(index_page_text, config)
        canonical_entries = [
            (CANONICAL_BOOK_TITLES[_normalize_title(title)], page)
            for title, page in entries
            if _normalize_title(title) in CANONICAL_BOOK_TITLES
        ]
        if len(canonical_entries) >= 10:
            entries = canonical_entries
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

        if not located_entries:
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
        candidates = list(range(min(10, book.page_count))) + list(range(max(0, book.page_count - 10), book.page_count))
        for index in dict.fromkeys(candidates):
            text = book.page_texts[index]
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            head_lines = lines[:3]
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
                    if title:
                        entries.append((title, page))
        return entries

    def _clean_title(self, value: str) -> str:
        value = re.split(r"(?:\s\.\s){2,}|\.{2,}", value)[0]
        value = re.sub(r"\s+", " ", value).strip(" .-_")
        for token in ["  Gn", "  Ex", "  Lv", "  Nm", "  Dt", "  Jos", "  Jdg", "  Ru", "  1Sm", "  2Sm", "  1Kg", "  2Kg", "  1Ch", "  2Ch", "  Ezr", "  Neh", "  Est", "  Jb", "  Ps", "  Pr", "  Ec", "  Sg", "  Is", "  Jr", "  Lm", "  Ezk", "  Dn", "  Hs", "  Jl", "  Am", "  Ob", "  Jnh", "  Mc", "  Nah", "  Hab", "  Zph", "  Hg", "  Zch", "  Mal", "  Mt", "  Mk", "  Lk", "  Jn", "  Ac", "  Rm", "  1Co", "  2Co", "  Gl", "  Eph", "  Php", "  Col", "  1T h", "  2Th", "  1T m", "  2Tm", "  Ti", "  Phm", "  Heb", "  Jms", "  1Pt", "  2Pt", "  1Jn", "  2Jn", "  3Jn", "  Jd", "  Rv"]:
            if value.endswith(token):
                value = value[: -len(token)].strip(" .-_")
        normalized = _normalize_title(value)
        for known_title, canonical in sorted(CANONICAL_BOOK_TITLES.items(), key=lambda item: len(item[0]), reverse=True):
            if normalized.startswith(known_title):
                return canonical
        return value

    def _find_title_page(self, book: BookDocument, title: str) -> int | None:
        normalized_title = _normalize_title(title)
        for page_number, text in enumerate(book.page_texts, start=1):
            first_line = _normalize_title(_first_non_empty_line(text))
            prefix = _normalize_title(" ".join(text.splitlines()[:2]))
            if first_line.startswith(normalized_title) or prefix.startswith(normalized_title):
                return page_number
        return None
