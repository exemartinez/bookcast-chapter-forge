from __future__ import annotations

from pathlib import Path

import yaml

from bookcast_chapter_forge.domain.entities import ParserConfig


class ConfigLoader:
    def load(self, path: str | Path) -> ParserConfig:
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        fixed_page = payload.get("fixed_page", {})
        regex = payload.get("regex", {})
        index = payload.get("index", {})
        max_pages = int(fixed_page.get("max_pages_per_chunk", 1))
        if max_pages <= 0:
            raise ValueError("fixed_page.max_pages_per_chunk must be greater than zero")

        return ParserConfig(
            max_pages_per_chunk=max_pages,
            regex_book_patterns=self._normalize(regex.get("book_patterns", [])),
            regex_english_patterns=self._normalize(regex.get("english_patterns", [])),
            regex_chapter_start_patterns=self._normalize(regex.get("chapter_start_patterns", [])),
            regex_chapter_end_patterns=self._normalize(regex.get("chapter_end_patterns", [])),
            regex_book_start_patterns=self._normalize(regex.get("book_start_patterns", [])),
            regex_book_end_patterns=self._normalize(regex.get("book_end_patterns", [])),
            index_title_patterns=self._normalize(index.get("index_title_patterns", [])),
            index_entry_patterns=self._normalize(index.get("entry_patterns", [])),
        )

    def _normalize(self, values: list[str]) -> tuple[str, ...]:
        return tuple(str(value).replace("\\\\", "\\") for value in values)
