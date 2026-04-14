from __future__ import annotations

from pathlib import Path

from bookcast_chapter_forge.domain.entities import ExecutionPreview, InteractiveRunRequest, SelectableBookEntry

SUPPORTED_BOOK_SUFFIXES = {".pdf"}
STRATEGY_CHOICES = ("adaptive", "fixed", "regex", "index", "layout", "semantic", "model", "heuristic", "llm")
CANCEL_TOKENS = {"q", "quit", "exit", "cancel"}


def ensure_books_dir(books_dir: str | Path) -> Path:
    """Create the books directory if it does not already exist."""
    path = Path(books_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def discover_selectable_books(books_dir: str | Path) -> tuple[SelectableBookEntry, ...]:
    """Return supported book files from the books directory in deterministic order."""
    root = ensure_books_dir(books_dir)
    paths = sorted(
        path for path in root.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_BOOK_SUFFIXES
    )
    return tuple(
        SelectableBookEntry(index=index, path=path, label=path.name)
        for index, path in enumerate(paths, start=1)
    )


def build_execution_preview(request: InteractiveRunRequest) -> ExecutionPreview:
    """Create the final interactive execution preview from one run request."""
    return ExecutionPreview(
        input_path=request.input_path,
        strategy=request.strategy,
        config_path=request.config_path,
        output_dir=request.output_dir,
        json_output=request.json_output,
    )


def format_execution_preview(preview: ExecutionPreview) -> str:
    """Format the execution preview shown before the final confirmation."""
    return "\n".join(
        [
            "Execution preview:",
            f"  input: {preview.input_path}",
            f"  strategy: {preview.strategy}",
            f"  config: {preview.config_path}",
            f"  output: {preview.output_dir}",
            f"  json: {'yes' if preview.json_output else 'no'}",
        ]
    )


def is_cancel(value: str) -> bool:
    """Return whether one interactive answer means the user wants to abort."""
    return value.strip().lower() in CANCEL_TOKENS
