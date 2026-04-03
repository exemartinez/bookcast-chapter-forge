from __future__ import annotations

import json
from pathlib import Path

from bookcast_chapter_forge.cli.pdf_parser import main


def test_cli_splits_a_two_page_pdf(blank_pdf_factory, tmp_path: Path) -> None:
    pdf_path = blank_pdf_factory("cli.pdf", 2)

    exit_code = main(
        [
            "--input",
            str(pdf_path),
            "--config",
            "configs/config.yaml",
            "--strategy",
            "fixed",
            "--output-dir",
            str(tmp_path / "out"),
            "--json",
        ]
    )

    assert exit_code == 0
    outputs = sorted((tmp_path / "out").glob("*.pdf"))
    assert len(outputs) == 2


def test_cli_accepts_regex_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "regex"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "regex", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "regex"


def test_cli_accepts_index_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "index"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "index", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "index"
