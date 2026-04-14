from __future__ import annotations

from pathlib import Path

from bookcast_chapter_forge.cli import interactive_cli


def _prompt_from(values: list[str]):
    iterator = iter(values)
    return lambda _: next(iterator)


def test_interactive_wrapper_delegates_to_parser_backend(blank_pdf_factory, tmp_path: Path, monkeypatch) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    pdf_path = blank_pdf_factory("wrapper.pdf", 1)
    pdf_path.replace(books_dir / "wrapper.pdf")
    calls = {}

    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            calls["strategy"] = strategy
            calls["config_path"] = config_path
            calls["input_path"] = input_path
            calls["books_dir"] = books_dir
            return []

    monkeypatch.setattr(interactive_cli, "build_service", lambda output_dir="output": FakeService())
    monkeypatch.chdir(tmp_path)

    exit_code = interactive_cli.main(
        prompt=_prompt_from(["1", "adaptive", "", "", "", "y"]),
        output=lambda *_args, **_kwargs: None,
    )

    assert exit_code == 0
    assert calls["strategy"] == "adaptive"
    assert calls["config_path"] == Path("configs/config.yaml")
    assert calls["input_path"] == books_dir / "wrapper.pdf"
    assert calls["books_dir"] is None


def test_interactive_wrapper_reports_empty_books_dir(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = interactive_cli.main(prompt=_prompt_from([]))

    assert exit_code == 0
    assert (tmp_path / "books").exists()
    assert "No supported book files were found" in capsys.readouterr().out


def test_interactive_wrapper_collects_core_options(blank_pdf_factory, tmp_path: Path, monkeypatch) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    pdf_path = blank_pdf_factory("wrapper.pdf", 1)
    pdf_path.replace(books_dir / "wrapper.pdf")
    calls = {}

    class FakeService:
        def process(self, strategy, config_path, input_path=None, books_dir=None):
            calls["strategy"] = strategy
            calls["config_path"] = config_path
            calls["input_path"] = input_path
            return []

    monkeypatch.setattr(interactive_cli, "build_service", lambda output_dir="output": FakeService())
    monkeypatch.chdir(tmp_path)

    exit_code = interactive_cli.main(
        prompt=_prompt_from(["1", "regex", "alt-config.yaml", "custom-output", "n", "y"]),
        output=lambda *_args, **_kwargs: None,
    )

    assert exit_code == 0
    assert calls["strategy"] == "regex"
    assert calls["config_path"] == Path("alt-config.yaml")
    assert calls["input_path"] == books_dir / "wrapper.pdf"
