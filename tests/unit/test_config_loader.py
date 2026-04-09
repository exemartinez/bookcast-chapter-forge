from __future__ import annotations

from pathlib import Path

import pytest

from bookcast_chapter_forge.services.config_loader import ConfigLoader


def test_loads_fixed_page_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fixed_page:\n  max_pages_per_chunk: 3\n", encoding="utf-8")

    config = ConfigLoader().load(config_path)

    assert config.max_pages_per_chunk == 3


def test_rejects_non_positive_max_pages(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fixed_page:\n  max_pages_per_chunk: 0\n", encoding="utf-8")

    with pytest.raises(ValueError):
        ConfigLoader().load(config_path)


def test_loads_regex_and_index_patterns(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "fixed_page:",
                "  max_pages_per_chunk: 2",
                "regex:",
                "  chapter_start_patterns:",
                "    - '(?i)^chapter'",
                "index:",
                "  index_title_patterns:",
                "    - '(?i)^contents$'",
                "  entry_patterns:",
                "    - '^(?P<title>.+?)[. ]+(?P<page>\\d+)$'",
            ]
        ),
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_path)

    assert config.regex_chapter_start_patterns == ("(?i)^chapter",)
    assert config.index_title_patterns == ("(?i)^contents$",)


def test_loads_optional_strategy_sections(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "fixed_page:",
                "  max_pages_per_chunk: 2",
                "layout:",
                "  heading_patterns:",
                "    - '(?i)^chapter'",
                "semantic:",
                "  title_patterns:",
                "    - '(?i)^part'",
                "model:",
                "  enabled: true",
                "heuristic:",
                "  signal_weights:",
                "    layout: 3.0",
                "    semantic: 2.0",
                "llm:",
                "  provider: ollama",
                "  model: phi3.5",
                "  timeout_seconds: 12",
                "  review_window: 2",
                "  max_excerpt_chars: 180",
            ]
        ),
        encoding="utf-8",
    )

    config = ConfigLoader().load(config_path)

    assert config.layout_heading_patterns == ("(?i)^chapter",)
    assert config.semantic_title_patterns == ("(?i)^part",)
    assert config.model_enabled is True
    assert config.heuristic_signal_weights["layout"] == 3.0
    assert config.llm_provider == "ollama"
    assert config.llm_model == "phi3.5"
    assert config.llm_timeout_seconds == 12.0
    assert config.llm_review_window == 2
    assert config.llm_max_excerpt_chars == 180


def test_rejects_invalid_llm_window(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "fixed_page:",
                "  max_pages_per_chunk: 2",
                "llm:",
                "  review_window: -1",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="llm.review_window"):
        ConfigLoader().load(config_path)
