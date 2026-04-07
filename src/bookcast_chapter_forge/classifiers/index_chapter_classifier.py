from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median

from pypdf import PdfReader

from bookcast_chapter_forge.classifiers.base import ChapterClassifier
from bookcast_chapter_forge.classifiers.regex_chapter_classifier import _normalize_title
from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk, ClassificationResult, ParserConfig

ROMAN_TOKEN_PATTERN = re.compile(r"^(?i:[ivxlcdm]+)$")
PAGE_TOKEN_AT_END_PATTERN = re.compile(r"(?:^|[\s.·_-])(?P<page>\d+|[ivxlcdm]+)\s*$", re.IGNORECASE)
MAJOR_FRONT_MATTER_TITLES = {
    "acknowledgment",
    "acknowledgement",
    "foreword",
    "preface",
    "introduction",
    "prologue",
    "epilogue",
    "conclusion",
    "appendix",
}


@dataclass(frozen=True)
class TocEntry:
    title: str
    page_token: str | None = None
    actual_page: int | None = None


class IndexChapterClassifier(ChapterClassifier):
    @property
    def strategy_name(self) -> str:
        return "index"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        reader = PdfReader(str(book.path))
        toc_page_indices = self._find_index_page_indices(book, reader, config)
        text_entries = self._parse_entries_from_text_pages(book, toc_page_indices, config)
        annotation_entries = self._parse_entries_from_annotations(book, reader, toc_page_indices, config)
        entries = self._merge_entries(text_entries, annotation_entries)
        if not entries:
            raise ValueError("No index entries could be parsed from the document")

        page_labels = tuple(str(label).strip() for label in getattr(reader, "page_labels", ()) or ())
        located_entries, offset_metadata = self._locate_entries(book, page_labels, entries, toc_page_indices)
        if len(located_entries) < 2:
            raise ValueError("No chapter starts could be located from the parsed index entries")

        monotonic_entries = self._keep_monotonic_entries(located_entries)
        chunks: list[ChapterChunk] = []
        for order, (title, page) in enumerate(monotonic_entries, start=1):
            next_page = monotonic_entries[order][1] if order < len(monotonic_entries) else book.page_count + 1
            chunks.append(ChapterChunk(order=order, start_page=page, end_page=next_page - 1, title=title))

        metadata = {"strategy": self.strategy_name, "toc_pages": len(toc_page_indices)}
        metadata.update(offset_metadata)
        return ClassificationResult(chunks=tuple(chunks), metadata=metadata)

    def _find_index_page_indices(self, book: BookDocument, reader: PdfReader, config: ParserConfig) -> list[int]:
        candidates = list(range(min(12, book.page_count))) + list(range(max(0, book.page_count - 12), book.page_count))
        start_index: int | None = None
        for index in dict.fromkeys(candidates):
            lines = self._non_empty_lines(book.page_texts[index])
            head_lines = lines[:4]
            if any(re.search(pattern, line) for pattern in config.index_title_patterns for line in head_lines):
                start_index = index
                break
            if any("contents" in line.lower() or line.lower() == "index" for line in head_lines):
                start_index = index
                break
        if start_index is None:
            raise ValueError("No valid index page was identified")

        toc_pages = [start_index]
        for index in range(start_index + 1, min(start_index + 6, book.page_count)):
            page = reader.pages[index]
            lines = self._non_empty_lines(book.page_texts[index])
            if (page.get("/Annots") and len(page.get("/Annots")) >= 3) or self._looks_like_toc_continuation(lines):
                toc_pages.append(index)
            else:
                break
        return toc_pages

    def _parse_entries_from_text_pages(self, book: BookDocument, toc_page_indices: list[int], config: ParserConfig) -> list[TocEntry]:
        entries: list[TocEntry] = []
        for index in toc_page_indices:
            lines = self._non_empty_lines(book.page_texts[index])
            line_index = 0
            while line_index < len(lines):
                line = lines[line_index]
                if self._is_toc_header(line):
                    line_index += 1
                    continue

                parsed = self._parse_text_entry_line(line, config)
                if parsed:
                    entries.append(parsed)
                    line_index += 1
                    continue

                if line_index + 1 < len(lines):
                    next_line = lines[line_index + 1]
                    if self._should_join_toc_lines(line, next_line):
                        parsed_joined = self._parse_text_entry_line(f"{line} {next_line}", config)
                        if parsed_joined:
                            entries.append(parsed_joined)
                            line_index += 2
                            continue

                line_index += 1
        return entries

    def _parse_entries_from_annotations(
        self,
        book: BookDocument,
        reader: PdfReader,
        toc_page_indices: list[int],
        config: ParserConfig,
    ) -> list[TocEntry]:
        entries: list[TocEntry] = []
        for index in toc_page_indices:
            page = reader.pages[index]
            annots = page.get("/Annots") or []
            if not annots:
                continue

            lines = [line for line in self._non_empty_lines(book.page_texts[index]) if not self._is_toc_header(line)]
            destinations = self._annotation_destinations(reader, annots)
            for line, actual_page in zip(lines, destinations):
                title = self._clean_title(line)
                if self._looks_like_major_toc_entry(title, config):
                    entries.append(TocEntry(title=title, actual_page=actual_page))
        return entries

    def _locate_entries(
        self,
        book: BookDocument,
        page_labels: tuple[str, ...],
        entries: list[TocEntry],
        toc_page_indices: list[int],
    ) -> tuple[list[tuple[str, int]], dict[str, int]]:
        excluded_page_numbers = {index + 1 for index in toc_page_indices}
        direct_arabic_offsets: list[int] = []
        direct_roman_offsets: list[int] = []
        located_entries: list[tuple[str, int]] = []

        for entry in entries:
            title_match_page = self._find_title_page(book, entry.title, excluded_page_numbers)
            label_match_page = self._find_page_by_label(page_labels, entry.page_token)

            if title_match_page is not None and entry.page_token:
                if self._is_roman(entry.page_token):
                    direct_roman_offsets.append(title_match_page - self._roman_to_int(entry.page_token))
                elif entry.page_token.isdigit():
                    direct_arabic_offsets.append(title_match_page - int(entry.page_token))

            actual_page = entry.actual_page or title_match_page or label_match_page
            located_entries.append((entry.title, actual_page or 0))

        arabic_offset = round(median(direct_arabic_offsets)) if direct_arabic_offsets else None
        roman_offset = round(median(direct_roman_offsets)) if direct_roman_offsets else None

        resolved_entries: list[tuple[str, int]] = []
        for entry, actual_page in zip(entries, located_entries):
            page = actual_page[1] or entry.actual_page
            if not page and entry.page_token:
                if entry.page_token.isdigit() and arabic_offset is not None:
                    page = int(entry.page_token) + arabic_offset
                elif self._is_roman(entry.page_token) and roman_offset is not None:
                    page = self._roman_to_int(entry.page_token) + roman_offset
                else:
                    page = self._find_page_by_label(page_labels, entry.page_token)
            if page and 1 <= page <= book.page_count:
                resolved_entries.append((entry.title, page))

        metadata: dict[str, int] = {}
        if arabic_offset is not None:
            metadata["page_offset"] = arabic_offset
        if roman_offset is not None:
            metadata["roman_page_offset"] = roman_offset
        return resolved_entries, metadata

    def _merge_entries(self, text_entries: list[TocEntry], annotation_entries: list[TocEntry]) -> list[TocEntry]:
        merged: dict[str, TocEntry] = {}
        for entry in text_entries + annotation_entries:
            normalized = _normalize_title(entry.title)
            existing = merged.get(normalized)
            if existing is None:
                merged[normalized] = entry
                continue
            merged[normalized] = TocEntry(
                title=existing.title if len(existing.title) >= len(entry.title) else entry.title,
                page_token=existing.page_token or entry.page_token,
                actual_page=existing.actual_page or entry.actual_page,
            )
        return list(merged.values())

    def _keep_monotonic_entries(self, entries: list[tuple[str, int]]) -> list[tuple[str, int]]:
        deduped_by_page: list[tuple[str, int]] = []
        seen_pages: set[int] = set()
        for title, page in sorted(entries, key=lambda item: item[1]):
            if page in seen_pages:
                continue
            if deduped_by_page and page <= deduped_by_page[-1][1]:
                continue
            deduped_by_page.append((title, page))
            seen_pages.add(page)
        return deduped_by_page

    def _parse_text_entry_line(self, line: str, config: ParserConfig) -> TocEntry | None:
        for pattern in config.index_entry_patterns:
            match = re.search(pattern, line)
            if match:
                title = self._clean_title(match.group("title"))
                page_token = match.group("page").strip()
                if len(_normalize_title(title)) >= 2:
                    return TocEntry(title=title, page_token=page_token)

        fallback = PAGE_TOKEN_AT_END_PATTERN.search(line)
        if not fallback:
            return None
        title = self._clean_title(line[: fallback.start("page")])
        if len(_normalize_title(title)) < 2:
            return None
        return TocEntry(title=title, page_token=fallback.group("page"))

    def _annotation_destinations(self, reader: PdfReader, annots) -> list[int]:
        destinations: list[int] = []
        for annot_ref in sorted(annots, key=lambda ref: (-float(ref.get_object().get("/Rect")[3]), float(ref.get_object().get("/Rect")[0]))):
            annot = annot_ref.get_object()
            dest = annot.get("/Dest")
            if not dest:
                continue
            dest_obj = dest[0]
            target_index = next(
                (
                    page_index
                    for page_index, candidate_page in enumerate(reader.pages)
                    if candidate_page.indirect_reference and candidate_page.indirect_reference.idnum == dest_obj.idnum
                ),
                None,
            )
            if target_index is not None:
                destinations.append(target_index + 1)
        return destinations

    def _find_page_by_label(self, page_labels: tuple[str, ...], page_token: str | None) -> int | None:
        if not page_token or not page_labels:
            return None
        normalized_token = page_token.lower()
        matches = [index + 1 for index, label in enumerate(page_labels) if label.lower() == normalized_token]
        return matches[0] if len(matches) == 1 else None

    def _find_title_page(self, book: BookDocument, title: str, excluded_page_numbers: set[int]) -> int | None:
        normalized_title = _normalize_title(title)
        for page_number, text in enumerate(book.page_texts, start=1):
            if page_number in excluded_page_numbers:
                continue
            first_lines = [self._clean_title(line) for line in text.splitlines()[:6] if line.strip()]
            normalized_lines = [_normalize_title(line) for line in first_lines if line]
            if any(line == normalized_title for line in normalized_lines):
                return page_number
            if any(line.startswith(normalized_title) or line.endswith(normalized_title) for line in normalized_lines):
                return page_number
            if any("page" in line and normalized_title in line for line in normalized_lines):
                return page_number
        return None

    def _looks_like_major_toc_entry(self, line: str, config: ParserConfig) -> bool:
        stripped = self._clean_title(line)
        if not stripped:
            return False
        normalized = _normalize_title(stripped)
        patterns = list(config.regex_chapter_start_patterns) + list(config.regex_book_start_patterns)
        if any(re.search(pattern, stripped) for pattern in patterns):
            return True
        return normalized in MAJOR_FRONT_MATTER_TITLES

    def _looks_like_toc_continuation(self, lines: list[str]) -> bool:
        if len(lines) < 3:
            return False
        chapter_like = sum(1 for line in lines if self._looks_like_heading_text(line))
        numbered_lines = sum(1 for line in lines if PAGE_TOKEN_AT_END_PATTERN.search(line))
        return chapter_like >= 1 or numbered_lines >= 2

    def _looks_like_heading_text(self, line: str) -> bool:
        lowered = line.lower()
        return any(keyword in lowered for keyword in ("chapter", "part", "section", "contents", "introduction", "preface"))

    def _should_join_toc_lines(self, line: str, next_line: str) -> bool:
        if PAGE_TOKEN_AT_END_PATTERN.search(line):
            return False
        if not PAGE_TOKEN_AT_END_PATTERN.search(next_line):
            return False
        if not self._looks_like_title_fragment(line):
            return False
        return True

    def _looks_like_title_fragment(self, line: str) -> bool:
        lowered = line.lower()
        if len(line) > 120:
            return False
        if any(header in lowered for header in ("contents", "table of contents", "index")):
            return False
        return bool(re.search(r"[A-Za-z]$", line))

    def _is_toc_header(self, line: str) -> bool:
        lowered = line.lower()
        return lowered in {"table of contents", "contents", "index", "old testament", "new testament", "additional material"} or lowered.startswith("books of the bible")

    def _clean_title(self, value: str) -> str:
        normalized = value.replace("\u00b7", ".")
        normalized = re.sub(r"\.{2,}", " ", normalized)
        normalized = re.sub(r"[_-]{2,}", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip(" .-_")

    def _non_empty_lines(self, text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _is_roman(self, value: str) -> bool:
        return bool(ROMAN_TOKEN_PATTERN.match(value.strip()))

    def _roman_to_int(self, value: str) -> int:
        numerals = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
        total = 0
        previous = 0
        for char in reversed(value.lower()):
            current = numerals[char]
            if current < previous:
                total -= current
            else:
                total += current
                previous = current
        return total
