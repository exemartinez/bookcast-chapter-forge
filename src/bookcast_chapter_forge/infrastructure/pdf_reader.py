from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from bookcast_chapter_forge.domain.entities import BookDocument


class PdfReaderAdapter:
    def read_book(self, path: str | Path) -> BookDocument:
        pdf_path = Path(path)
        reader = PdfReader(str(pdf_path))
        texts = tuple((page.extract_text() or "") for page in reader.pages)
        return BookDocument(path=pdf_path, page_texts=texts, title=pdf_path.stem)

    def page_count(self, path: str | Path) -> int:
        reader = PdfReader(str(path))
        return len(reader.pages)
