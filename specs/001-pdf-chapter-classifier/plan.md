# Implementation Plan: PDF Chapter Classifier

**Branch**: `001-pdf-chapter-classifier` | **Date**: 2026-04-03 | **Spec**: `specs/001-pdf-chapter-classifier/spec.md`
**Input**: Feature specification from `/specs/001-pdf-chapter-classifier/spec.md`

## Summary

Build a small Python CLI that reads PDF files from the repo `books/` folder or a direct input path, validates that the file is a PDF, computes chunk boundaries, and writes one output PDF per chunk into `output/`. The implementation should start with a deterministic page-count chunking mode, then add a regex-based `ChapterClassifier` strategy, and finally add an index-driven strategy. The system stays intentionally simple: file-based, local-only, object-oriented, and organized around a parser service plus interchangeable chunking strategies.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pypdf` for PDF reading/writing, `PyYAML` for config loading, Python `argparse`, `dataclasses`, `logging`, `pathlib`, `re`  
**Storage**: Local filesystem only (`books/`, `configs/`, `output/`)  
**Testing**: `pytest`, `pytest-cov`  
**Target Platform**: macOS/Linux CLI environment  
**Project Type**: Single-package CLI application  
**Performance Goals**: Process common book PDFs sequentially with visible progress and complete chunk writing without partial output on interruption or classification failure  
**Constraints**: Offline-capable, OO-first design, structured logs to stdout/stderr, graceful `Ctrl-C`, no partial persisted output on failed runs, keep v1 simple and file-based  
**Scale/Scope**: One repository, one CLI, sequential processing of local PDF files, initial support limited to English-language heuristics

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `OO-first`: Pass. Core behavior will be centered on classes and strategy interfaces, not script-only procedural logic.
- `CLI interface`: Pass. Primary entrypoint is a CLI command with human-readable output and optional JSON mode for machine consumption.
- `Test-first`: Pass, with execution note. Implementation must be sequenced as tests first for each slice: page chunking, parser orchestration, classifier strategies, and interrupt/rollback behavior.
- `Observability`: Pass. Use structured logging with consistent event names and context fields.
- `Versioning / breaking changes`: Pass. This is a new feature with no public API to preserve yet.
- `Simplicity`: Pass. No database, queue, service boundary, or premature plugin system.

No constitution violations are required for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/001-pdf-chapter-classifier/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── bookcast_chapter_forge/
    ├── cli/
    │   └── pdf_parser.py
    ├── domain/
    │   ├── entities.py
    │   └── results.py
    ├── services/
    │   ├── pdf_parser_service.py
    │   ├── output_writer.py
    │   └── config_loader.py
    ├── classifiers/
    │   ├── base.py
    │   ├── fixed_page_classifier.py
    │   ├── regex_chapter_classifier.py
    │   └── index_chapter_classifier.py
    └── infrastructure/
        ├── pdf_reader.py
        └── logging.py

configs/
└── config.yaml

books/

output/

tests/
├── unit/
│   ├── test_config_loader.py
│   ├── test_fixed_page_classifier.py
│   ├── test_regex_chapter_classifier.py
│   ├── test_index_chapter_classifier.py
│   └── test_output_writer.py
├── integration/
│   ├── test_pdf_parser_cli.py
│   └── test_pdf_parser_service.py
└── fixtures/
    └── pdfs/
```

**Structure Decision**: Use a single Python package with a thin CLI layer, explicit domain entities, and strategy-based classifier modules. This matches the constitution, keeps the app portfolio-friendly, and avoids unnecessary service or package splitting.

## Implementation Design

### Core Objects

- `BookDocument`: metadata and source path for one PDF.
- `ChapterChunk`: chunk order, optional chapter name, start page, end page, output filename stem.
- `ParserConfig`: validated runtime config loaded from YAML.
- `ClassificationResult`: ordered collection of `ChapterChunk` definitions plus warnings/metadata.
- `ChapterClassifier`: strategy interface returning chunk boundaries for a `BookDocument`.
- `FixedPageClassifier`: splits by configured maximum page count.
- `RegexChapterClassifier`: identifies start/end pages using configurable regex patterns.
- `IndexChapterClassifier`: derives chapter boundaries from index pages and page-number offset detection.
- `PdfParserService`: orchestrates validation, classification, progress logging, and output writing.
- `OutputWriter`: writes chunk PDFs to a temporary location, then promotes them into `output/` only on success.

### CLI Surface

- Command: `python -m bookcast_chapter_forge.cli.pdf_parser`
- Inputs:
  - `--input <path>` for a single PDF
  - `--books-dir <path>` defaulting to `books/`
  - `--config <path>` defaulting to `configs/config.yaml`
  - `--strategy fixed|regex|index`
  - `--json` for machine-readable summary output
- Exit behavior:
  - `0` on success
  - non-zero on validation, classification, config, or write failure
  - `Ctrl-C` aborts safely with cleanup and no partial final output

### Delivery Phases

1. P1 MVP:
   Implement fixed-page chunking with config-driven page size, single-file and folder processing, deterministic naming, progress logs, and atomic output writing.
2. P2 classifier:
   Add regex-driven classification heuristics for book/chapter boundaries and batch processing over `books/`.
3. P3 strategy refinement:
   Add index-page strategy, chapter-name-based filenames, and explicit strategy selection in the CLI.

## Work Plan

### Phase 0 Research

- Confirm the PDF library API for reading page text and writing subsets without lossy page order changes.
- Define the minimum YAML schema required for fixed, regex, and index strategies.
- Confirm a practical atomic-write approach for `output/` rollback on failure or `Ctrl-C`.
- Record tradeoffs for regex heuristics versus index-based heuristics in `research.md`.

### Phase 1 Design

- Define domain entities and classifier interface in `data-model.md`.
- Write CLI usage and developer workflow in `quickstart.md`.
- Define CLI contract and JSON output contract in `contracts/`.
- Finalize config schema:
  - `fixed_page.max_pages_per_chunk`
  - `regex.book_patterns`
  - `regex.english_patterns`
  - `regex.chapter_start_patterns`
  - `regex.chapter_end_patterns`
  - `regex.book_start_patterns`
  - `regex.book_end_patterns`
  - `index.index_title_patterns`
  - `index.entry_patterns`
- Re-run constitution check against the concrete design before implementation.

### Phase 2 Implementation

- Set up package structure, CLI entrypoint, and dependency manifest.
- Implement config loading and validation.
- Implement PDF reader and output writer abstractions.
- Implement fixed-page chunking strategy.
- Implement parser orchestration for single file and folder processing.
- Add structured logging and progress reporting.
- Implement regex-based classifier strategy.
- Implement index-based classifier strategy.
- Add filename sanitization and chapter-name truncation.

### Phase 3 Verification

- Unit test each classifier independently with fixture PDFs or mocked page text.
- Integration test end-to-end CLI behavior for:
  - fixed-page mode on a two-page sample PDF
  - folder processing over multiple PDFs
  - interrupt handling and no final partial output
  - invalid config and invalid input file handling
- Add coverage for filename generation and config parsing edge cases.

## Test-First Execution Order

Because the constitution makes TDD non-negotiable, implementation should be sliced in this order:

1. Write failing tests for config loading and fixed-page chunk creation.
2. Implement minimum code to pass fixed-page chunking tests.
3. Write failing integration tests for CLI-driven PDF splitting and atomic output behavior.
4. Implement parser orchestration and output writing.
5. Write failing tests for regex classification.
6. Implement regex classifier.
7. Write failing tests for index-page extraction and offset calculation.
8. Implement index classifier.
9. Refactor only behind existing passing tests.

## Risks and Mitigations

- PDF text extraction may be inconsistent across source files.
  - Mitigation: keep heuristics configurable in YAML and log classification evidence per page.
- Regex chapter detection may misclassify front matter or appendices.
  - Mitigation: keep fixed-page mode as a fallback and expose strategy selection explicitly.
- Atomic rollback can be broken by writing directly into final output paths.
  - Mitigation: always write to a temporary run directory and rename/move only after full success.
- The Bible test fixture may have page-number offsets that differ from printed index values.
  - Mitigation: make offset calculation a first-class responsibility of the index strategy.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
