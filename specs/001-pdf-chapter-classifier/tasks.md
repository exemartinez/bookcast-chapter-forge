# Tasks: PDF Chapter Classifier

**Input**: Design documents from `specs/001-pdf-chapter-classifier/`
**Prerequisites**: `specs/001-pdf-chapter-classifier/plan.md` (required), `specs/001-pdf-chapter-classifier/spec.md` (required for user stories)

**Tests**: Tests are required for this feature because the constitution makes TDD mandatory and `spec.md` includes independent test expectations for each user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package layout, tool configuration, and baseline repo files needed by all stories.

- [X] T001 Create the package and test directory structure rooted at `src/bookcast_chapter_forge/`, `tests/unit/`, `tests/integration/`, and `tests/fixtures/pdfs/`
- [X] T002 Initialize runtime and test dependency metadata in `requirements.txt`
- [X] T003 [P] Create package marker files in `src/bookcast_chapter_forge/__init__.py`, `src/bookcast_chapter_forge/cli/__init__.py`, `src/bookcast_chapter_forge/domain/__init__.py`, `src/bookcast_chapter_forge/services/__init__.py`, `src/bookcast_chapter_forge/classifiers/__init__.py`, and `src/bookcast_chapter_forge/infrastructure/__init__.py`
- [X] T004 [P] Create the initial YAML configuration file in `configs/config.yaml`
- [X] T005 [P] Add a pytest configuration file in `pytest.ini`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the core OO model, filesystem safety, configuration loading, and logging primitives that every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create core domain dataclasses `BookDocument`, `ChapterChunk`, `ParserConfig`, and `ClassificationResult` in `src/bookcast_chapter_forge/domain/entities.py`
- [X] T007 [P] Create the classifier strategy interface in `src/bookcast_chapter_forge/classifiers/base.py`
- [X] T008 [P] Implement config loading and validation in `src/bookcast_chapter_forge/services/config_loader.py`
- [X] T009 [P] Implement PDF reading and page text extraction helpers in `src/bookcast_chapter_forge/infrastructure/pdf_reader.py`
- [X] T010 [P] Implement structured logging helpers in `src/bookcast_chapter_forge/infrastructure/logging.py`
- [X] T011 Implement atomic output writing with temporary directories and rollback support in `src/bookcast_chapter_forge/services/output_writer.py`
- [X] T012 Implement parser orchestration skeleton and cancellation-safe cleanup hooks in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [X] T013 Implement the CLI argument parser and top-level command flow in `src/bookcast_chapter_forge/cli/pdf_parser.py`

**Checkpoint**: Foundation ready. User story implementation can now begin.

---

## Phase 3: User Story 1 - Fixed-Page PDF Chunking (Priority: P1) 🎯 MVP

**Goal**: Split one input PDF into sequential PDF chunks using a configured maximum page count.

**Independent Test**: Run the CLI against a two-page sample PDF with `fixed_page.max_pages_per_chunk: 1` and verify that `output/` contains exactly two one-page PDFs.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Add config loader tests for fixed-page settings in `tests/unit/test_config_loader.py`
- [X] T015 [P] [US1] Add fixed-page classifier unit tests for chunk boundary generation in `tests/unit/test_fixed_page_classifier.py`
- [X] T016 [P] [US1] Add output writer unit tests for atomic success and rollback behavior in `tests/unit/test_output_writer.py`
- [X] T017 [P] [US1] Add CLI integration test for splitting a two-page sample PDF in `tests/integration/test_pdf_parser_cli.py`
- [X] T018 [P] [US1] Add parser service integration test for single-file processing in `tests/integration/test_pdf_parser_service.py`

### Implementation for User Story 1

- [X] T019 [US1] Implement `FixedPageClassifier` in `src/bookcast_chapter_forge/classifiers/fixed_page_classifier.py`
- [X] T020 [US1] Implement single-file PDF validation and fixed-page chunk generation in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [X] T021 [US1] Implement fixed-page CLI execution flow and progress output in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [X] T022 [US1] Implement deterministic output file naming `{input file name}-{order number}.pdf` in `src/bookcast_chapter_forge/services/output_writer.py`
- [X] T023 [US1] Add interrupt handling for `Ctrl-C` with final output rollback in `src/bookcast_chapter_forge/services/pdf_parser_service.py`

**Checkpoint**: User Story 1 is fully functional as the MVP.

---

## Phase 4: User Story 2 - Generic Regex-Based Chapter Classification (Priority: P2)

**Goal**: Add a generic `ChapterClassifier`-driven mode that identifies chapter boundaries for English books without relying on domain-specific hardcoded title catalogs.

**Independent Test**: Run the CLI in regex mode against at least one general English book with ordinary chapter headings and verify that output chunks start at real chapter boundaries.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Add unit tests for generic heading-pattern chapter detection in `tests/unit/test_regex_chapter_classifier.py`
- [X] T025 [P] [US2] Add unit tests proving the default regex strategy does not depend on domain-specific hardcoded title catalogs in `tests/unit/test_regex_chapter_classifier.py`
- [X] T026 [P] [US2] Add integration test for folder-based processing through `books/` in `tests/integration/test_pdf_parser_service.py`
- [X] T027 [P] [US2] Add CLI integration test for regex strategy selection in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 2

- [X] T028 [US2] Refactor `configs/config.yaml` so regex settings describe generic English-book structural patterns in `configs/config.yaml`
- [X] T029 [US2] Remove domain-specific hardcoded title catalogs and implement generic heading detection in `src/bookcast_chapter_forge/classifiers/regex_chapter_classifier.py`
- [X] T030 [US2] Add confidence-based validation for generic English-book chapter detection in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [X] T031 [US2] Add `books/` directory batch processing support to `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [X] T032 [US2] Add progress logging for generic heading inference and identified chapter boundaries in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [X] T033 [US2] Enforce “PDF and book only” validation before writing outputs in `src/bookcast_chapter_forge/services/pdf_parser_service.py`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Generic Index-Based Classification Strategy (Priority: P3)

**Goal**: Add a generic contents/index-driven strategy that detects English TOC pages, derives chapter names and page offsets, and emits chapter-named output files.

**Independent Test**: Run the CLI in index mode against at least one English book with a usable table of contents and verify that output chunks align with TOC-derived chapter starts.

### Tests for User Story 3 ⚠️

- [X] T034 [P] [US3] Add unit tests for generic contents-page identification and entry parsing in `tests/unit/test_index_chapter_classifier.py`
- [X] T035 [P] [US3] Add unit tests for generic page-offset calculation, Roman-numeral TOC handling, and chapter-name extraction in `tests/unit/test_index_chapter_classifier.py`
- [X] T036 [P] [US3] Add unit tests for filename sanitization and chapter-name truncation in `tests/unit/test_output_writer.py`
- [X] T037 [P] [US3] Add CLI integration test for index strategy execution in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 3

- [X] T038 [US3] Refactor `configs/config.yaml` so index settings describe generic English TOC layouts in `configs/config.yaml`
- [X] T039 [US3] Replace the current index resolver with local-window TOC parsing from text lines, Roman numerals, clickable TOC destinations, and outline/bookmark fallbacks in `src/bookcast_chapter_forge/classifiers/index_chapter_classifier.py`
- [X] T040 [US3] Add robust offset-based chunk generation that derives bounds from the current and next TOC entries inside local search windows in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [X] T041 [US3] Add chapter-name-aware output naming `{input file name}-{order number}-{chapter name (max 10 characters)}.pdf` in `src/bookcast_chapter_forge/services/output_writer.py`
- [X] T042 [US3] Update the CLI strategy selector and user-facing progress output for index classification in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [X] T043 [US3] Abort processing with a clear error when no valid index page is identified in `src/bookcast_chapter_forge/classifiers/index_chapter_classifier.py`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, validation, and documentation across all stories.

- [X] T044 [P] Update CLI usage and configuration documentation for generic English-book chapter detection in `README.md`
- [X] T045 [P] Add JSON summary output support in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [X] T046 Normalize end-to-end error reporting in `src/bookcast_chapter_forge/cli/pdf_parser.py` and `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [X] T047 [P] Add missing generic-book edge-case coverage, including clickable TOCs, Roman-numeral contents, local-window heading resolution, KJV Ezra ordering, and LLM chapter-sequence regressions in `tests/unit/test_config_loader.py`, `tests/unit/test_regex_chapter_classifier.py`, `tests/unit/test_index_chapter_classifier.py`, and `tests/integration/test_index_real_books.py`
- [X] T048 Run and verify the full test suite plus real index-strategy validation for Roman-numeral contents, clickable TOCs, local-window heading resolution, and offset accuracy from `tests/unit/` and `tests/integration/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies, can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion and reuses the parser/output foundation from US1
- **User Story 3 (Phase 5)**: Depends on Foundational completion and conceptually builds on the strategy model introduced in US2
- **Polish (Phase 6)**: Depends on completion of the desired user stories

### User Story Dependencies

- **User Story 1 (P1)**: First deliverable and MVP
- **User Story 2 (P2)**: Depends on the parser orchestration and CLI shell already established for US1
- **User Story 3 (P3)**: Depends on the generic strategy model established by US2

### Within Each User Story

- Tests must be written and observed failing before implementation
- Config and entities before classifier/service behavior
- Classifier behavior before CLI integration
- Output naming and rollback behavior before story sign-off

### Parallel Opportunities

- T003, T004, and T005 can run in parallel during setup
- T007, T008, T009, and T010 can run in parallel during foundational work
- Within each story, test tasks marked `[P]` can run in parallel
- Within each story, config-file and classifier implementation tasks can proceed in parallel when they touch different files

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 tests together:
Task: "Add config loader tests for fixed-page settings in tests/unit/test_config_loader.py"
Task: "Add fixed-page classifier unit tests for chunk boundary generation in tests/unit/test_fixed_page_classifier.py"
Task: "Add output writer unit tests for atomic success and rollback behavior in tests/unit/test_output_writer.py"

# Launch independent implementation tasks together after tests exist:
Task: "Implement FixedPageClassifier in src/bookcast_chapter_forge/classifiers/fixed_page_classifier.py"
Task: "Implement fixed-page CLI execution flow and progress output in src/bookcast_chapter_forge/cli/pdf_parser.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate the fixed-page chunking workflow end-to-end

### Incremental Delivery

1. Deliver fixed-page chunking as the first usable CLI slice
2. Add regex-based chapter classification as the second increment
3. Add index-based chapter classification and chapter-name output naming as the third increment
4. Finish with polish, JSON output, and documentation cleanup

### Parallel Team Strategy

With multiple developers:

1. One developer handles foundational domain and infrastructure files
2. One developer focuses on tests and fixtures for each story first
3. Once the foundation is stable, classifier strategy work can split between regex and index implementations

---

## Notes

- `[P]` tasks are intended for different files with minimal coupling
- Every task uses repository-relative paths and is derived only from `plan.md` and `spec.md`, which are the currently available design documents
- `tasks.md` intentionally follows the constitution’s OO-first and test-first constraints
- US2 and US3 were reopened and are now reimplemented around generic English-book heuristics rather than Bible-specific title catalogs
