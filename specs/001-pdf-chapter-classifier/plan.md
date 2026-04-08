# Implementation Plan: PDF Chapter Classifier

**Branch**: `001-pdf-chapter-classifier` | **Date**: 2026-04-07 | **Spec**: `specs/001-pdf-chapter-classifier/spec.md`
**Input**: Feature specification from `specs/001-pdf-chapter-classifier/spec.md`

## Summary

Build a Python CLI that splits PDFs into NotebookLM-ready chunks. The MVP remains fixed-page chunking, but the main feature goal is generic chapter identification for English books. The default chapter-detection strategies must work on ordinary books without domain-specific hardcoded title catalogs. The implementation should favor configurable structural heuristics, contents-page parsing, and strategy-based composition over corpus-specific fallback lists.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pypdf`, `PyYAML`, Python `argparse`, `dataclasses`, `logging`, `pathlib`, `re`  
**Storage**: Local filesystem only (`books/`, `configs/`, `output/`)  
**Testing**: `pytest`, `pytest-cov`  
**Target Platform**: macOS/Linux CLI environment  
**Project Type**: Single-package CLI application  
**Performance Goals**: Process book PDFs sequentially with visible progress and write no partial final output on failure or interruption  
**Constraints**: Offline-capable, OO-first design, structured logs, `Ctrl-C` rollback, generic English-book heuristics by default, no domain-specific hardcoded title catalogs in the default regex or index strategies  
**Scale/Scope**: One repository, one CLI, sequential local PDF processing, English books only for v1 generic chapter detection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `OO-first`: Pass. Strategies and services remain explicit classes.
- `CLI interface`: Pass. Primary interface remains CLI-first.
- `Test-first`: Pass. Strategy changes must be implemented behind tests.
- `Observability`: Pass. Structured logs remain required.
- `Versioning / breaking changes`: Pass. We are still within initial feature development.
- `Simplicity`: Pass. Generic heuristics are preferred over domain plugins in the default flow.

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
    │   └── entities.py
    ├── services/
    │   ├── config_loader.py
    │   ├── output_writer.py
    │   └── pdf_parser_service.py
    ├── classifiers/
    │   ├── base.py
    │   ├── fixed_page_classifier.py
    │   ├── regex_chapter_classifier.py
    │   └── index_chapter_classifier.py
    └── infrastructure/
        ├── logging.py
        └── pdf_reader.py

configs/
└── config.yaml

tests/
├── unit/
└── integration/
```

**Structure Decision**: Keep the existing single-package structure, but change classifier behavior so the default strategies are generic and config-driven rather than corpus-specific.

## Implementation Design

### Core Objects

- `BookDocument`: source path, page texts, optional title
- `ChapterChunk`: output slice with order, page boundaries, optional chapter name
- `ParserConfig`: validated chunking and heuristic configuration
- `ClassificationResult`: ordered chunk boundaries plus metadata/warnings
- `ChapterClassifier`: strategy interface
- `FixedPageClassifier`: deterministic page-count fallback
- `RegexChapterClassifier`: generic heading-pattern classifier for English books
- `IndexChapterClassifier`: generic contents-page classifier with page-offset inference
- `PdfParserService`: orchestration, validation, logging, rollback-safe writing
- `OutputWriter`: atomic write/promote behavior

### Strategy Design Changes

- Remove domain-specific hardcoded title catalogs from the default regex classifier.
- Infer likely chapter starts from generic signals:
  - heading keywords such as `chapter`, `part`, `section`, `prologue`, `epilogue`
  - repeated heading layouts across pages
  - title-only heading pages
  - configurable structural patterns in `config.yaml`
- Parse contents pages generically from common English TOC layouts and treat the parsed TOC text as the authoritative list of chunk titles.
- Support Roman-numeral contents entries for front matter and similar sections.
- Fall back to clickable TOC hyperlink destinations when text extraction does not expose printable page numbers, but only to fill targets for titles already found in TOC text.
- Infer offsets from multiple anchors so a single title-page mismatch does not shift the whole book by one page.
- Resolve each TOC entry inside a bounded candidate window around the inferred page instead of scanning the entire document.
- Use page-local heading extraction that favors larger-font text when matching chapter titles inside that window.
- If domain-specific profiles are needed later, isolate them as explicit optional profiles rather than default behavior.

### CLI Surface

- Command remains `python -m bookcast_chapter_forge.cli.pdf_parser`
- Strategies remain `fixed|regex|index`
- `regex` and `index` now mean generic English-book strategies, not Bible-oriented strategies

## Delivery Phases

1. P1 MVP:
   Preserve fixed-page chunking as a deterministic fallback.
2. P2 generic regex classifier:
   Replace corpus-specific fallback behavior with generic English-book heading detection.
3. P3 generic index classifier:
   Implement generic contents-page parsing, Roman-numeral support, hyperlink-aware TOC mapping, robust page-offset matching, and windowed heading resolution for English books.

## Work Plan

### Phase 0 Research

- Identify common chapter-heading patterns across ordinary English books.
- Identify generic TOC/contents layouts worth supporting in v1.
- Record rejection criteria for low-confidence chapter detection.

### Phase 1 Design

- Redesign regex heuristics around generic heading signals.
- Redesign index parsing around generic contents-page patterns.
- Include hyperlink-driven TOC handling and Roman-numeral page-label handling in the index design.
- Update `config.yaml` schema to favor generic structural patterns instead of corpus-specific title lists.

### Phase 2 Implementation

- Keep fixed-page strategy intact.
- Refactor regex classifier to remove domain-specific hardcoded title catalogs.
- Refactor index classifier to parse generic contents pages and use that TOC text as the authoritative chunk list.
- Refactor index classifier to resolve TOC entries from text, page labels, and hyperlink destinations, but only as supplements for already-parsed TOC titles.
- Build chunk boundaries by resolving the current entry and the next entry separately inside local search windows and deriving page ranges from that pair.
- Update validation, logging, and output naming as needed.

### Phase 3 Verification

- Add tests for generic books with chapter headings.
- Add tests for generic TOC-based books.
- Add tests for Roman-numeral TOC entries, clickable TOC entries, and off-by-one offset regressions.
- Add tests for local-window heading resolution so nearby repeated titles do not capture the wrong distant page.
- Add tests that extra outline-only or annotation-only entries do not create unwanted chunks.
- Keep failure-mode tests for invalid PDFs, non-book-like inputs, and rollback behavior.

## Test-First Execution Order

1. Write failing tests that prove the regex classifier no longer depends on domain-specific hardcoded title catalogs.
2. Write failing tests for generic English-book heading detection.
3. Implement and refactor the regex classifier until tests pass.
4. Write failing tests for generic contents-page parsing.
5. Implement and refactor the index classifier until tests pass.
6. Re-run end-to-end CLI validation and rollback tests.

## Risks and Mitigations

- Generic heuristics may be less precise than corpus-specific fallback logic.
  - Mitigation: prefer clear failure over silent misclassification and keep heuristics configurable.
- Some books may have weak or inconsistent chapter formatting.
  - Mitigation: keep fixed-page mode available and document limits of automatic detection.
- Contents pages vary widely.
  - Mitigation: support the most common English layouts first and fail explicitly when parsing confidence is low.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
