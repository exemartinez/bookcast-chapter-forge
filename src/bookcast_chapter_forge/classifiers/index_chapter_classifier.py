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


@dataclass(frozen=True)
class HeadingMatch:
    page_number: int
    has_leading_text: bool


@dataclass(frozen=True)
class FontFragment:
    text: str
    font_size: float
    order: int


@dataclass(frozen=True)
class PageAnalysis:
    full_text: str
    first_lines: tuple[str, ...]
    fragments: tuple[FontFragment, ...]
    largest_font_texts: tuple[str, ...]


class IndexChapterClassifier(ChapterClassifier):
    window_size = 10

    @property
    def strategy_name(self) -> str:
        return "index"

    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        reader = PdfReader(str(book.path))
        page_labels = tuple(str(label).strip() for label in getattr(reader, "page_labels", ()) or ())
        toc_page_indices = self._find_index_page_indices(book, reader, config)
        entries = self._collect_entries(book, reader, toc_page_indices, config)
        if not entries:
            raise ValueError("No index entries could be parsed from the document")

        analysis_cache: dict[int, PageAnalysis] = {}
        offsets = self._infer_offsets(book, reader, entries, toc_page_indices, page_labels, analysis_cache)
        chunks = self._build_chunks(book, reader, entries, page_labels, offsets, analysis_cache, toc_page_indices)
        if len(chunks) < 2:
            raise ValueError("No chapter starts could be located from the parsed index entries")

        metadata: dict[str, str | int] = {"strategy": self.strategy_name, "toc_pages": len(toc_page_indices)}
        metadata.update(offsets)
        return ClassificationResult(chunks=tuple(chunks), metadata=metadata)

    def _build_chunks(
        self,
        book: BookDocument,
        reader: PdfReader,
        entries: list[TocEntry],
        page_labels: tuple[str, ...],
        offsets: dict[str, int],
        analysis_cache: dict[int, PageAnalysis],
        toc_page_indices: list[int],
    ) -> list[ChapterChunk]:
        chunks: list[ChapterChunk] = []
        last_end_page = 0
        excluded_page_numbers: set[int] = {page_index + 1 for page_index in toc_page_indices}

        for index, entry in enumerate(entries):
            candidate_page = self._candidate_page(entry, page_labels, offsets)
            if candidate_page is None:
                candidate_page = self._find_heading_globally(reader, book, entry.title, excluded_page_numbers, analysis_cache)
            if candidate_page is None:
                continue

            begin_match = self._find_heading_in_window(reader, book, entry.title, candidate_page, analysis_cache, excluded_page_numbers)
            begin_page = begin_match.page_number if begin_match else candidate_page
            begin_page = min(max(1, begin_page), book.page_count)

            if index + 1 < len(entries):
                next_entry = entries[index + 1]
                next_candidate_page = self._candidate_page(next_entry, page_labels, offsets)
                if next_candidate_page is None:
                    next_candidate_page = self._find_heading_globally(reader, book, next_entry.title, excluded_page_numbers, analysis_cache)
                if next_candidate_page is None:
                    next_candidate_page = min(book.page_count, begin_page + self.window_size + 1)
                next_match = self._find_heading_in_window(reader, book, next_entry.title, next_candidate_page, analysis_cache, excluded_page_numbers)
                if next_match:
                    end_page = next_match.page_number if next_match.has_leading_text else next_match.page_number - 1
                else:
                    end_page = next_candidate_page - 1
            else:
                end_page = book.page_count

            begin_page = max(begin_page, last_end_page + 1 if last_end_page else begin_page)
            begin_page = min(book.page_count, max(1, begin_page))
            end_page = min(book.page_count, max(begin_page, end_page))
            if begin_page > book.page_count or end_page < begin_page:
                continue

            chunk = ChapterChunk(order=len(chunks) + 1, start_page=begin_page, end_page=end_page, title=entry.title)
            if not chunks or chunk.start_page > chunks[-1].start_page:
                chunks.append(chunk)
                last_end_page = chunk.end_page

        return chunks

    def _infer_offsets(
        self,
        book: BookDocument,
        reader: PdfReader,
        entries: list[TocEntry],
        toc_page_indices: list[int],
        page_labels: tuple[str, ...],
        analysis_cache: dict[int, PageAnalysis],
    ) -> dict[str, int]:
        excluded_page_numbers = {page_index + 1 for page_index in toc_page_indices}
        arabic_offsets: list[int] = []
        roman_offsets: list[int] = []

        for entry in entries:
            if not entry.page_token:
                continue

            anchor_page = entry.actual_page
            if anchor_page is None:
                anchor_page = self._find_heading_globally(reader, book, entry.title, excluded_page_numbers, analysis_cache)
            if anchor_page is None:
                anchor_page = self._find_page_by_label(page_labels, entry.page_token)
            if anchor_page is None:
                continue

            if self._is_roman(entry.page_token):
                roman_offsets.append(anchor_page - self._roman_to_int(entry.page_token))
            elif entry.page_token.isdigit():
                arabic_offsets.append(anchor_page - int(entry.page_token))

        metadata: dict[str, int] = {}
        if arabic_offsets:
            metadata["page_offset"] = round(median(arabic_offsets))
        if roman_offsets:
            metadata["roman_page_offset"] = round(median(roman_offsets))
        return metadata

    def _candidate_page(self, entry: TocEntry, page_labels: tuple[str, ...], offsets: dict[str, int]) -> int | None:
        if entry.actual_page is not None:
            return entry.actual_page
        if not entry.page_token:
            return None

        label_match = self._find_page_by_label(page_labels, entry.page_token)
        if entry.page_token.isdigit() and "page_offset" in offsets:
            return int(entry.page_token) + offsets["page_offset"]
        if self._is_roman(entry.page_token) and "roman_page_offset" in offsets:
            return self._roman_to_int(entry.page_token) + offsets["roman_page_offset"]
        return label_match

    def _collect_entries(
        self,
        book: BookDocument,
        reader: PdfReader,
        toc_page_indices: list[int],
        config: ParserConfig,
    ) -> list[TocEntry]:
        """Collect TOC titles from text first, then enrich only those titles with page targets."""
        text_entries = self._parse_entries_from_text_pages(book, toc_page_indices, config)
        annotation_entries = self._parse_entries_from_annotations(book, reader, toc_page_indices, config)
        outline_entries = self._parse_entries_from_outline(reader, config)
        return self._merge_entries(text_entries, annotation_entries, outline_entries)

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

                title_only = self._parse_title_only_entry_line(line, config)
                if title_only:
                    entries.append(title_only)
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

    def _parse_entries_from_outline(self, reader: PdfReader, config: ParserConfig) -> list[TocEntry]:
        outline = getattr(reader, "outline", None) or []
        entries_by_title: dict[str, TocEntry] = {}
        for item in self._flatten_outline(outline):
            title = self._clean_title(item.get("/Title", ""))
            if not title or not self._looks_like_major_toc_entry(title, config):
                continue
            page_ref = item.get("/Page")
            if page_ref is None:
                continue
            target_index = next(
                (
                    page_index
                    for page_index, candidate_page in enumerate(reader.pages)
                    if candidate_page.indirect_reference and candidate_page.indirect_reference.idnum == page_ref.idnum
                ),
                None,
            )
            if target_index is not None:
                normalized = _normalize_title(title)
                actual_page = target_index + 1
                existing = entries_by_title.get(normalized)
                if existing is None or actual_page > (existing.actual_page or 0):
                    entries_by_title[normalized] = TocEntry(title=title, actual_page=actual_page)
        return list(entries_by_title.values())

    def _merge_entries(
        self,
        text_entries: list[TocEntry],
        annotation_entries: list[TocEntry],
        outline_entries: list[TocEntry],
    ) -> list[TocEntry]:
        """Supplement parsed TOC titles with targets; never invent extra chunk titles from metadata alone."""
        merged = list(text_entries)
        for source_entry in annotation_entries + outline_entries:
            normalized_annotation = _normalize_title(source_entry.title)
            merged_index = next(
                (
                    index
                    for index, existing in enumerate(merged)
                    if _normalize_title(existing.title) == normalized_annotation
                ),
                None,
            )
            if merged_index is None:
                continue

            existing = merged[merged_index]
            if existing.actual_page is not None and source_entry.actual_page is not None:
                if (source_entry.actual_page or 0) > (existing.actual_page or 0):
                    merged[merged_index] = TocEntry(
                        title=existing.title if len(existing.title) >= len(source_entry.title) else source_entry.title,
                        page_token=existing.page_token or source_entry.page_token,
                        actual_page=source_entry.actual_page,
                    )
                continue
            merged[merged_index] = TocEntry(
                title=existing.title if len(existing.title) >= len(source_entry.title) else source_entry.title,
                page_token=existing.page_token or source_entry.page_token,
                actual_page=source_entry.actual_page or existing.actual_page,
            )
        return merged

    def _find_heading_in_window(
        self,
        reader: PdfReader,
        book: BookDocument,
        title: str,
        candidate_page: int,
        analysis_cache: dict[int, PageAnalysis],
        excluded_page_numbers: set[int],
    ) -> HeadingMatch | None:
        window_start = max(1, candidate_page - self.window_size)
        window_end = min(book.page_count, candidate_page + self.window_size)
        for page_number in range(window_start, window_end + 1):
            if page_number in excluded_page_numbers:
                continue
            analysis = self._page_analysis(reader, book, page_number, analysis_cache)
            if self._page_matches_title(analysis, title):
                return HeadingMatch(page_number=page_number, has_leading_text=self._page_has_leading_text(analysis, title))
        return None

    def _find_heading_globally(
        self,
        reader: PdfReader,
        book: BookDocument,
        title: str,
        excluded_page_numbers: set[int],
        analysis_cache: dict[int, PageAnalysis],
    ) -> int | None:
        for page_number in range(1, book.page_count + 1):
            if page_number in excluded_page_numbers:
                continue
            analysis = self._page_analysis(reader, book, page_number, analysis_cache)
            if self._page_matches_title(analysis, title, strong_only=True):
                return page_number
        return None

    def _page_analysis(
        self,
        reader: PdfReader,
        book: BookDocument,
        page_number: int,
        analysis_cache: dict[int, PageAnalysis],
    ) -> PageAnalysis:
        if page_number in analysis_cache:
            return analysis_cache[page_number]

        full_text = book.page_texts[page_number - 1]
        fragments: list[FontFragment] = []
        order = 0

        def visitor(text, _cm, tm, _font_dict, font_size):
            nonlocal order
            if text and text.strip():
                fragments.append(FontFragment(text=text.strip(), font_size=float(font_size or 0), order=order))
                order += 1

        try:
            reader.pages[page_number - 1].extract_text(visitor_text=visitor)
        except Exception:
            fragments = []

        grouped_texts: list[str] = []
        if fragments:
            grouped: dict[float, list[str]] = {}
            for fragment in fragments:
                rounded_size = round(fragment.font_size, 2)
                grouped.setdefault(rounded_size, []).append(fragment.text)
            for font_size in sorted(grouped, reverse=True)[:3]:
                grouped_texts.append(" ".join(grouped[font_size]))

        analysis = PageAnalysis(
            full_text=full_text,
            first_lines=tuple(self._non_empty_lines(full_text)[:6]),
            fragments=tuple(sorted(fragments, key=lambda fragment: fragment.order)),
            largest_font_texts=tuple(grouped_texts),
        )
        analysis_cache[page_number] = analysis
        return analysis

    def _page_matches_title(self, analysis: PageAnalysis, title: str, strong_only: bool = False) -> bool:
        title_pattern = self._title_pattern(title)
        priority_texts = analysis.largest_font_texts or analysis.first_lines
        if any(title_pattern.search(_normalize_title(text)) for text in priority_texts):
            return True
        if any(title_pattern.search(_normalize_title(line)) for line in analysis.first_lines):
            return True
        if strong_only:
            return False
        return bool(title_pattern.search(_normalize_title(analysis.full_text)))

    def _page_has_leading_text(self, analysis: PageAnalysis, title: str) -> bool:
        title_pattern = self._title_pattern(title)
        if analysis.fragments:
            matched_index: int | None = None
            for index, fragment in enumerate(analysis.fragments):
                if title_pattern.search(_normalize_title(fragment.text)):
                    matched_index = index
                    break
            if matched_index is not None:
                return any(any(char.isalnum() for char in fragment.text) for fragment in analysis.fragments[:matched_index])

        matched_line_index = next(
            (index for index, line in enumerate(analysis.first_lines) if title_pattern.search(_normalize_title(line))),
            None,
        )
        if matched_line_index is not None:
            return matched_line_index > 0
        return False

    def _title_pattern(self, title: str) -> re.Pattern[str]:
        normalized = _normalize_title(title)
        escaped_parts = [re.escape(part) for part in normalized.split()]
        pattern = r"(?<![a-z0-9])" + r"\s+".join(escaped_parts) + r"(?![a-z0-9])"
        return re.compile(pattern, re.IGNORECASE)

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

    def _parse_title_only_entry_line(self, line: str, config: ParserConfig) -> TocEntry | None:
        """Accept title-only TOC lines only when they look like numbered chapter entries."""
        title = self._clean_title(line)
        if not title:
            return None
        chapter_patterns = tuple(pattern for pattern in config.regex_chapter_start_patterns if "introduction" not in pattern.lower() and "conclusion" not in pattern.lower())
        if any(re.search(pattern, title) for pattern in chapter_patterns):
            return TocEntry(title=title)
        return None

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

    def _flatten_outline(self, outline_items) -> list[dict]:
        flattened: list[dict] = []
        for item in outline_items:
            if isinstance(item, list):
                flattened.extend(self._flatten_outline(item))
            elif isinstance(item, dict):
                flattened.append(item)
        return flattened

    def _find_page_by_label(self, page_labels: tuple[str, ...], page_token: str | None) -> int | None:
        if not page_token or not page_labels:
            return None
        normalized_token = page_token.lower()
        matches = [index + 1 for index, label in enumerate(page_labels) if label.lower() == normalized_token]
        return matches[0] if len(matches) == 1 else None

    def _looks_like_major_toc_entry(self, line: str, config: ParserConfig) -> bool:
        stripped = self._clean_title(line)
        if not stripped:
            return False
        normalized = _normalize_title(stripped)
        chapter_patterns = tuple(pattern for pattern in config.regex_chapter_start_patterns if "introduction" not in pattern.lower() and "conclusion" not in pattern.lower())
        if any(re.search(pattern, stripped) for pattern in chapter_patterns):
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
