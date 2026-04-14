from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable

from bookcast_chapter_forge.cli.pdf_parser import build_service
from bookcast_chapter_forge.domain.entities import InteractiveRunRequest, SelectableBookEntry
from bookcast_chapter_forge.services.interactive_runner import (
    STRATEGY_CHOICES,
    build_execution_preview,
    discover_selectable_books,
    format_execution_preview,
    is_cancel,
)

PromptFunc = Callable[[str], str]
PrintFunc = Callable[..., None]


def _prompt_select_book(entries: tuple[SelectableBookEntry, ...], prompt: PromptFunc, output: PrintFunc) -> Path | None:
    output("Available books:")
    for entry in entries:
        output(f"  {entry.index}. {entry.label}")
    while True:
        answer = prompt("Select a file number (or 'q' to cancel): ").strip()
        if is_cancel(answer):
            return None
        if answer.isdigit():
            selected = int(answer)
            for entry in entries:
                if entry.index == selected:
                    return entry.path
        output("Invalid selection. Enter one of the listed numbers or 'q' to cancel.")


def _prompt_strategy(prompt: PromptFunc, output: PrintFunc, default: str = "adaptive") -> str | None:
    output("Available strategies:")
    for index, strategy in enumerate(STRATEGY_CHOICES, start=1):
        marker = " (default)" if strategy == default else ""
        output(f"  {index}. {strategy}{marker}")
    while True:
        answer = prompt(f"Choose strategy [{default}] (or 'q' to cancel): ").strip()
        if not answer:
            return default
        if is_cancel(answer):
            return None
        if answer.isdigit():
            choice = int(answer)
            if 1 <= choice <= len(STRATEGY_CHOICES):
                return STRATEGY_CHOICES[choice - 1]
        if answer in STRATEGY_CHOICES:
            return answer
        output("Invalid strategy. Enter a listed number, strategy name, or 'q' to cancel.")


def _prompt_path(prompt: PromptFunc, label: str, default: Path) -> Path | None:
    answer = prompt(f"{label} [{default}] (or 'q' to cancel): ").strip()
    if not answer:
        return default
    if is_cancel(answer):
        return None
    return Path(answer)


def _prompt_json_mode(prompt: PromptFunc, output: PrintFunc, default: bool = True) -> bool | None:
    default_label = "Y/n" if default else "y/N"
    while True:
        answer = prompt(f"Emit JSON output? [{default_label}] (or 'q' to cancel): ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        if answer in {"q", "quit", "exit", "cancel"}:
            return None
        output("Invalid answer. Enter y, n, or 'q' to cancel.")


def collect_run_request(
    books_dir: str | Path = "books",
    default_config: str | Path = "configs/config.yaml",
    default_output: str | Path = "output",
    prompt: PromptFunc = input,
    output: PrintFunc = print,
) -> InteractiveRunRequest | None:
    """Collect one interactive run request from the user."""
    entries = discover_selectable_books(books_dir)
    if not entries:
        output(f"No supported book files were found in {Path(books_dir)}.")
        output("Add at least one PDF file to the books directory and try again.")
        return None

    selected_book = _prompt_select_book(entries, prompt, output)
    if selected_book is None:
        output("Interactive run cancelled.")
        return None

    strategy = _prompt_strategy(prompt, output)
    if strategy is None:
        output("Interactive run cancelled.")
        return None

    config_path = _prompt_path(prompt, "Config path", Path(default_config))
    if config_path is None:
        output("Interactive run cancelled.")
        return None

    output_dir = _prompt_path(prompt, "Output directory", Path(default_output))
    if output_dir is None:
        output("Interactive run cancelled.")
        return None

    json_output = _prompt_json_mode(prompt, output)
    if json_output is None:
        output("Interactive run cancelled.")
        return None

    request = InteractiveRunRequest(
        input_path=selected_book,
        strategy=strategy,
        config_path=config_path,
        output_dir=output_dir,
        json_output=json_output,
    )
    preview = build_execution_preview(request)
    output(format_execution_preview(preview))
    confirmation = prompt("Run parser with these settings? [y/N]: ").strip().lower()
    if confirmation not in {"y", "yes"}:
        output("Interactive run cancelled.")
        return None
    return request


def run_request(request: InteractiveRunRequest, service=None):
    """Delegate one confirmed interactive request to the existing parser backend."""
    parser_service = service or build_service(output_dir=request.output_dir)
    return parser_service.process(
        strategy=request.strategy,
        config_path=request.config_path,
        input_path=request.input_path,
    )


def main(argv: list[str] | None = None, prompt: PromptFunc = input, output: PrintFunc = print) -> int:
    """Run the interactive wrapper flow and delegate to the existing parser backend."""
    if argv:
        output("The interactive wrapper does not accept parser parameters.", file=sys.stderr)
        return 1

    request = collect_run_request(prompt=prompt, output=output)
    if request is None:
        return 0
    try:
        processed = run_request(request)
    except KeyboardInterrupt:
        output("Processing aborted by user", file=sys.stderr)
        return 130
    except Exception as exc:
        output(str(exc), file=sys.stderr)
        return 1

    output(f"Processed {len(processed)} book(s).")
    for item in processed:
        output(f"{item.source} -> {item.chunk_count} chunk(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
