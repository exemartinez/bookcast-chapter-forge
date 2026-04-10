# bookcast-chapter-forge Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-10

## Active Technologies
- Python 3.11 + `pypdf` for PDF reading/writing, `PyYAML` for config loading, Python `argparse`, `dataclasses`, `logging`, `pathlib`, `re` (001-pdf-chapter-classifier)
- Local filesystem only (`books/`, `configs/`, `output/`) (001-pdf-chapter-classifier)
- Python 3.11 + Existing: `pypdf`, `PyYAML`, `pytest`; Optional for this feature: `pymupdf4llm`, `unstructured`, `langchain` and/or `langgraph`, local model runtime (e.g., Ollama) (002-heuristic-chapter-detection)
- Python 3.11 + Existing: `pypdf`, `PyYAML`, `pytest`; Optional for this feature: `pymupdf4llm`, `unstructured`, `langchain-ollama` or a thin Ollama HTTP adapter, local `Ollama` runtime with `phi3.5` mini (002-heuristic-chapter-detection)
- Python 3.11 + Existing: `pypdf`, `PyYAML`, `pytest`; feature reuses existing parser service and `llama.cpp` `llama-server` integration from feature 002 (003-adaptive-strategy-fallback)

## Project Structure

```text
src/
tests/
```

## Commands

pytest
ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- 003-adaptive-strategy-fallback: Added Python 3.11 + Existing: `pypdf`, `PyYAML`, `pytest`; feature reuses existing parser service and `llama.cpp` `llama-server` integration from feature 002
- 003-adaptive-strategy-fallback: Added Python 3.11 + Existing: `pypdf`, `PyYAML`, `pytest`; feature reuses existing parser service and `llama.cpp` `llama-server` integration from feature 002
- 003-adaptive-strategy-fallback: Added Python 3.11 + Existing: `pypdf`, `PyYAML`, `pytest`; feature reuses existing parser service and `llama.cpp` `llama-server` integration from feature 002

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
