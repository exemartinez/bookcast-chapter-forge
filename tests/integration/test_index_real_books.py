from __future__ import annotations

from pathlib import Path

import pytest

from bookcast_chapter_forge.services.config_loader import ConfigLoader
from bookcast_chapter_forge.infrastructure.pdf_reader import PdfReaderAdapter
from bookcast_chapter_forge.classifiers.index_chapter_classifier import IndexChapterClassifier


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.slow
@pytest.mark.skipif(not (REPO_ROOT / "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf").exists(), reason="Fixture PDF not available")
def test_index_strategy_supports_hyperlinked_toc_book() -> None:
    path = REPO_ROOT / "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf"
    config = ConfigLoader().load(REPO_ROOT / "configs/config.yaml")
    book = PdfReaderAdapter().read_book(path)

    result = IndexChapterClassifier().classify(book, config)

    assert len(result.chunks) >= 10


@pytest.mark.slow
@pytest.mark.skipif(not (REPO_ROOT / "books/The-Holy-Bible-King-James-Version.pdf").exists(), reason="Fixture PDF not available")
def test_index_strategy_places_kjv_genesis_on_page_one_boundary() -> None:
    path = REPO_ROOT / "books/The-Holy-Bible-King-James-Version.pdf"
    config = ConfigLoader().load(REPO_ROOT / "configs/config.yaml")
    book = PdfReaderAdapter().read_book(path)

    result = IndexChapterClassifier().classify(book, config)

    assert result.chunks[0].title == "Genesis"
    assert result.chunks[0].start_page == 22


@pytest.mark.slow
@pytest.mark.skipif(not (REPO_ROOT / "books/The-Holy-Bible-King-James-Version.pdf").exists(), reason="Fixture PDF not available")
def test_index_strategy_keeps_ezra_between_chronicles_and_nehemiah() -> None:
    path = REPO_ROOT / "books/The-Holy-Bible-King-James-Version.pdf"
    config = ConfigLoader().load(REPO_ROOT / "configs/config.yaml")
    book = PdfReaderAdapter().read_book(path)

    result = IndexChapterClassifier().classify(book, config)
    titles = [chunk.title for chunk in result.chunks]

    ezra_index = titles.index("Ezra")
    assert titles[ezra_index - 1] == "2 Chronicles"
    assert titles[ezra_index + 1] == "Nehemiah"
    assert result.chunks[ezra_index].start_page == 294


@pytest.mark.slow
@pytest.mark.skipif(not (REPO_ROOT / "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf").exists(), reason="Fixture PDF not available")
def test_index_strategy_keeps_llm_chapter_sequence_without_false_subsections() -> None:
    path = REPO_ROOT / "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf"
    config = ConfigLoader().load(REPO_ROOT / "configs/config.yaml")
    book = PdfReaderAdapter().read_book(path)

    result = IndexChapterClassifier().classify(book, config)
    titles = [chunk.title for chunk in result.chunks]

    assert titles[:6] == [
        "Chapter I: Introduction to LLMs",
        "Chapter II: LLM Architectures and Landscape",
        "Chapter III: LLMs in Practice",
        "Chapter IV: Introduction to Prompting",
        "Chapter V: Retrieval-Augmented Generation",
        "Chapter VI: Introduction to LangChain & LlamaIndex",
    ]
    assert "Introduction to Large Multimodal Models" not in titles
    assert "Acknowledgment" not in titles
    assert "Preface" not in titles
    assert "Introduction" not in titles
    assert titles[6:12] == [
        "Chapter VII: Prompting with LangChain",
        "Chapter VIII: Indexes, Retrievers, and Data Preparation",
        "Chapter IX: Advanced RAG",
        "Chapter X: Agents",
        "Chapter XI: Fine-Tuning",
        "Chapter XII: Deployment and Optimization",
    ]
