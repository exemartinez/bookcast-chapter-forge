from __future__ import annotations

import json
from pathlib import Path

from bookcast_chapter_forge.cli.pdf_parser import main


def test_cli_splits_a_two_page_pdf(blank_pdf_factory, tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fixed_page:\n  max_pages_per_chunk: 1\n", encoding="utf-8")
    pdf_path = blank_pdf_factory("cli.pdf", 2)

    exit_code = main(
        [
            "--input",
            str(pdf_path),
            "--config",
            str(config_path),
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


def test_cli_accepts_layout_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "layout"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "layout", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "layout"


def test_cli_accepts_semantic_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "semantic"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "semantic", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "semantic"


def test_cli_accepts_model_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "model"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "model", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "model"


def test_cli_accepts_heuristic_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "heuristic"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "heuristic", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "heuristic"


def test_cli_accepts_llm_strategy_selection(monkeypatch, capsys) -> None:
    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            assert strategy == "llm"
            return []

    monkeypatch.setattr("bookcast_chapter_forge.cli.pdf_parser.build_service", lambda output_dir="output": FakeService())

    exit_code = main(["--strategy", "llm", "--json"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["strategy"] == "llm"
