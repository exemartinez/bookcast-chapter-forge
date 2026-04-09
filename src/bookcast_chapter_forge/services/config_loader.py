from __future__ import annotations

from pathlib import Path

import yaml

from bookcast_chapter_forge.domain.entities import ParserConfig


class ConfigLoader:
    """Loads and normalizes parser configuration from YAML."""

    def load(self, path: str | Path) -> ParserConfig:
        """Read the YAML file and convert it into the typed parser config."""
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        fixed_page = payload.get("fixed_page", {})
        regex = payload.get("regex", {})
        index = payload.get("index", {})
        layout = payload.get("layout", {})
        semantic = payload.get("semantic", {})
        model = payload.get("model", {})
        heuristic = payload.get("heuristic", {})
        llm = payload.get("llm", {})
        max_pages = int(fixed_page.get("max_pages_per_chunk", 1))
        if max_pages <= 0:
            raise ValueError("fixed_page.max_pages_per_chunk must be greater than zero")
        review_window = int(llm.get("review_window", 1))
        if review_window < 0:
            raise ValueError("llm.review_window must be zero or greater")
        max_excerpt_chars = int(llm.get("max_excerpt_chars", 300))
        if max_excerpt_chars <= 0:
            raise ValueError("llm.max_excerpt_chars must be greater than zero")
        timeout_seconds = float(llm.get("timeout_seconds", 30.0))
        if timeout_seconds <= 0:
            raise ValueError("llm.timeout_seconds must be greater than zero")

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
            layout_heading_patterns=self._normalize(layout.get("heading_patterns", [])),
            semantic_title_patterns=self._normalize(semantic.get("title_patterns", [])),
            model_enabled=bool(model.get("enabled", False)),
            heuristic_signal_weights=self._normalize_weights(heuristic.get("signal_weights", {})),
            llm_provider=str(llm.get("provider", "llama.cpp")),
            llm_model=str(llm.get("model", "ggml-org/gemma-3-1b-it-GGUF")),
            llm_base_url=str(llm.get("base_url", "http://127.0.0.1:8080")),
            llm_timeout_seconds=timeout_seconds,
            llm_review_window=review_window,
            llm_max_excerpt_chars=max_excerpt_chars,
            llm_prompt_instructions=str(llm.get("prompt_instructions", "")),
        )

    def _normalize(self, values: list[str]) -> tuple[str, ...]:
        """Unescape YAML-loaded regex strings into usable Python regex literals."""
        return tuple(str(value).replace("\\\\", "\\") for value in values)

    def _normalize_weights(self, weights: dict[str, object]) -> dict[str, float]:
        """Convert configured signal weights into a normalized float mapping."""
        return {str(key): float(value) for key, value in (weights or {}).items()}
