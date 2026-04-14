from __future__ import annotations

from pathlib import Path

from bookcast_chapter_forge.cli.interactive_cli import collect_run_request
from bookcast_chapter_forge.services.interactive_runner import (
    build_execution_preview,
    discover_selectable_books,
    format_execution_preview,
)


def _prompt_from(values: list[str]):
    iterator = iter(values)
    return lambda _: next(iterator)


def test_discover_selectable_books_creates_books_dir(tmp_path: Path) -> None:
    books_dir = tmp_path / "books"

    entries = discover_selectable_books(books_dir)

    assert books_dir.exists()
    assert entries == ()


def test_discover_selectable_books_is_deterministic(blank_pdf_factory, tmp_path: Path) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    blank_pdf_factory("zeta.pdf", 1).replace(books_dir / "zeta.pdf")
    blank_pdf_factory("alpha.pdf", 1).replace(books_dir / "alpha.pdf")

    entries = discover_selectable_books(books_dir)

    assert [entry.label for entry in entries] == ["alpha.pdf", "zeta.pdf"]


def test_collect_run_request_cancels_before_confirmation(blank_pdf_factory, tmp_path: Path) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    blank_pdf_factory("book one.pdf", 1).replace(books_dir / "book one.pdf")
    messages: list[str] = []

    request = collect_run_request(
        books_dir=books_dir,
        prompt=_prompt_from(["1", "adaptive", "", "", "", "n"]),
        output=messages.append,
    )

    assert request is None
    assert messages[-1] == "Interactive run cancelled."


def test_collect_run_request_builds_request_and_preview(blank_pdf_factory, tmp_path: Path) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    blank_pdf_factory("book one.pdf", 1).replace(books_dir / "book one.pdf")
    messages: list[str] = []

    request = collect_run_request(
        books_dir=books_dir,
        prompt=_prompt_from(["1", "2", "", "", "", "y"]),
        output=messages.append,
    )

    assert request is not None
    assert request.input_path == books_dir / "book one.pdf"
    assert request.strategy == "fixed"
    assert request.config_path == Path("configs/config.yaml")
    assert request.output_dir == Path("output")
    assert request.json_output is True
    assert any("Execution preview:" in message for message in messages)


def test_collect_run_request_handles_paths_with_spaces(blank_pdf_factory, tmp_path: Path) -> None:
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    blank_pdf_factory("Anna's Book 01.pdf", 1).replace(books_dir / "Anna's Book 01.pdf")
    request = collect_run_request(
        books_dir=books_dir,
        prompt=_prompt_from(["1", "adaptive", "", "", "", "y"]),
        output=lambda *_args, **_kwargs: None,
    )

    assert request is not None
    assert request.input_path.name == "Anna's Book 01.pdf"


def test_build_execution_preview_formats_readably(tmp_path: Path) -> None:
    from bookcast_chapter_forge.domain.entities import InteractiveRunRequest

    request = InteractiveRunRequest(
        input_path=tmp_path / "books" / "example.pdf",
        strategy="adaptive",
        config_path=Path("configs/config.yaml"),
        output_dir=Path("output"),
        json_output=True,
    )

    preview = build_execution_preview(request)
    rendered = format_execution_preview(preview)

    assert "input:" in rendered
    assert "strategy: adaptive" in rendered
    assert "json: yes" in rendered
