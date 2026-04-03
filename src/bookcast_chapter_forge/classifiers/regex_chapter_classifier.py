from __future__ import annotations

import re

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig

KNOWN_BOOK_TITLES = {
    "genesis",
    "exodus",
    "leviticus",
    "numbers",
    "deuteronomy",
    "joshua",
    "judges",
    "ruth",
    "1 samuel",
    "2 samuel",
    "1 kings",
    "2 kings",
    "1 chronicles",
    "2 chronicles",
    "ezra",
    "nehemiah",
    "esther",
    "job",
    "psalms",
    "proverbs",
    "ecclesiastes",
    "song of songs",
    "song of solomon",
    "isaiah",
    "jeremiah",
    "lamentations",
    "ezekiel",
    "daniel",
    "hosea",
    "joel",
    "amos",
    "obadiah",
    "jonah",
    "micah",
    "nahum",
    "habakkuk",
    "zephaniah",
    "haggai",
    "zechariah",
    "malachi",
    "matthew",
    "mark",
    "luke",
    "john",
    "acts",
    "romans",
    "1 corinthians",
    "2 corinthians",
    "galatians",
    "ephesians",
    "philippians",
    "colossians",
    "1 thessalonians",
    "2 thessalonians",
    "1 timothy",
    "2 timothy",
    "titus",
    "philemon",
    "hebrews",
    "james",
    "1 peter",
    "2 peter",
    "1 john",
    "2 john",
    "3 john",
    "jude",
    "revelation",
}


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def _normalize_title(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


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
        for page_number, text in enumerate(book.page_texts, start=1):
            first_line = _first_non_empty_line(text)
            page_prefix = "\n".join(text.splitlines()[:4]).strip()
            if self._matches_start(first_line, page_prefix, config):
                title = first_line or f"Chapter {page_number}"
                normalized = _normalize_title(title)
                if normalized and normalized != last_title:
                    starts.append((page_number, title))
                    last_title = normalized

        if not starts:
            raise ValueError("No chapter boundaries were identified by regex strategy")
        if len(starts) == 1 and starts[0][0] != 1 and book.page_count < 2:
            raise ValueError("The PDF does not appear to be a book")

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

    def _matches_start(self, first_line: str, page_prefix: str, config: ParserConfig) -> bool:
        haystacks = [first_line, page_prefix]
        patterns = list(config.regex_chapter_start_patterns) + list(config.regex_book_start_patterns)
        if any(re.search(pattern, haystack) for haystack in haystacks for pattern in patterns if haystack):
            return True
        normalized = _normalize_title(first_line)
        return any(normalized == title or normalized.startswith(f"{title} page") for title in KNOWN_BOOK_TITLES)
