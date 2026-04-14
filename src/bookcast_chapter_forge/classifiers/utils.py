from __future__ import annotations

import re

from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk


def first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def chapter_start_pages(book: BookDocument, patterns: tuple[str, ...]) -> list[tuple[int, str]]:
    starts: list[tuple[int, str]] = []
    for page_number, text in enumerate(book.page_texts, start=1):
        first_line = first_non_empty_line(text)
        if first_line and any(re.search(pattern, first_line) for pattern in patterns):
            starts.append((page_number, first_line))
    return starts


def build_chunks(starts: list[tuple[int, str]], page_count: int) -> tuple[ChapterChunk, ...]:
    if not starts:
        starts = [(1, "Chapter 1")]
    starts = sorted(starts, key=lambda item: item[0])
    chunks: list[ChapterChunk] = []
    for order, (start_page, title) in enumerate(starts, start=1):
        next_start = starts[order][0] if order < len(starts) else page_count + 1
        end_page = max(start_page, next_start - 1)
        chunks.append(ChapterChunk(order=order, start_page=start_page, end_page=end_page, title=title))
    return tuple(chunks)

