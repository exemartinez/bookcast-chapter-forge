from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from bookcast_chapter_forge.domain.entities import BookDocument, ChapterChunk


class OutputWriter:
    def __init__(self, output_dir: str | Path = "output") -> None:
        self.output_dir = Path(output_dir)

    def write_book_chunks(self, book: BookDocument, chunks: tuple[ChapterChunk, ...]) -> list[Path]:
        reader = PdfReader(str(book.path))
        temp_dir = Path(tempfile.mkdtemp(prefix="bookcast-", dir=self.output_dir.parent))
        written: list[Path] = []
        try:
            for chunk in chunks:
                filename = self.filename_for_chunk(book, chunk)
                temp_path = temp_dir / filename
                writer = PdfWriter()
                for index in range(chunk.start_page - 1, chunk.end_page):
                    writer.add_page(reader.pages[index])
                with temp_path.open("wb") as handle:
                    writer.write(handle)
                written.append(temp_path)

            self.output_dir.mkdir(parents=True, exist_ok=True)
            final_paths: list[Path] = []
            for temp_path in written:
                final_path = self.output_dir / temp_path.name
                shutil.move(str(temp_path), str(final_path))
                final_paths.append(final_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return final_paths
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def filename_for_chunk(self, book: BookDocument, chunk: ChapterChunk) -> str:
        base = f"{self.sanitize_filename(book.stem)}-{chunk.order:03d}"
        if chunk.title:
            title = self.shorten_title_slug(self.sanitize_filename(chunk.title))
            if title:
                base = f"{base}-{title}"
        return f"{base}.pdf"

    def sanitize_filename(self, value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]+", "-", value.strip())
        normalized = re.sub(r"-+", "-", normalized).strip("-")
        return normalized or "chunk"

    def shorten_title_slug(self, value: str) -> str:
        parts = value.split("-")
        if len(parts) >= 2 and parts[0].lower() in {"chapter", "part", "section", "book"}:
            return "-".join(parts[:2])[:20].rstrip("-")
        return value[:20].rstrip("-")
