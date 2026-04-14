# Tasks: Interactive CLI Wrapper

**Input**: Design documents from `specs/005-interactive-cli-wrapper/`  
**Prerequisites**: `specs/005-interactive-cli-wrapper/plan.md` (required), `specs/005-interactive-cli-wrapper/spec.md` (required for user stories)

**Tests**: Tests are required for this feature because constitution requires test-first work and each user story has independent test criteria.

**Organization**: Tasks are grouped by user story to support independent implementation and validation while preserving the required sequence `US1 -> US2 -> US3`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout at repository root: `src/`, `tests/`, `configs/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the launcher entrypoint and documentation surfaces for the interactive wrapper.

- [x] T001 Add `bookcast_forge.sh` launcher documentation in `README.md`
- [x] T002 [P] Add feature-005 release notes in `CHANGELOG.md`
- [x] T003 [P] Add placeholder launcher script at `bookcast_forge.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the interactive request model and wrapper entrypoint before story implementation begins.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [x] T004 Add interactive wrapper entities in `src/bookcast_chapter_forge/domain/entities.py`
- [x] T005 [P] Add interactive wrapper module scaffold in `src/bookcast_chapter_forge/cli/`
- [x] T006 [P] Add file-discovery and path-resolution support in `src/bookcast_chapter_forge/services/`
- [x] T007 [P] Add launcher wiring from `bookcast_forge.sh` into the Python interactive entrypoint

**Checkpoint**: Foundation complete; user stories can now be implemented in planned order.

---

## Phase 3: User Story 1 - Launch And Run The Parser Interactively (Priority: P1) - MVP

**Goal**: Launch a no-argument interactive wrapper, collect the minimum required choices, and run the existing parser backend after explicit confirmation.

**Independent Test**: Run `bookcast_forge.sh`, select one file and one strategy, confirm the preview, and verify the parser backend runs with those values.

### Tests for User Story 1

> **NOTE: Write these tests FIRST; ensure they fail before implementation.**

- [x] T008 [P] [US1] Add unit tests for interactive run request creation and execution preview formatting in `tests/unit/test_interactive_cli_wrapper.py`
- [x] T009 [P] [US1] Add unit tests for cancellation before confirmation in `tests/unit/test_interactive_cli_wrapper.py`
- [x] T010 [P] [US1] Add integration test for launching the interactive wrapper and delegating to the parser backend in `tests/integration/test_interactive_cli_launcher.py`

### Implementation for User Story 1

- [x] T011 [US1] Implement the Python interactive launcher module in `src/bookcast_chapter_forge/cli/`
- [x] T012 [US1] Implement execution preview and confirmation flow in `src/bookcast_chapter_forge/cli/` or `src/bookcast_chapter_forge/services/`
- [x] T013 [US1] Implement backend delegation to the existing parser service or CLI in `src/bookcast_chapter_forge/cli/`
- [x] T014 [US1] Finalize `bookcast_forge.sh` to run the interactive launcher with repository-relative defaults

**Checkpoint**: US1 is independently functional and can launch a confirmed parser run through the wrapper.

---

## Phase 4: User Story 2 - Select Inputs And Parameters Safely (Priority: P2)

**Goal**: Discover supported files from `books/`, create `books/` automatically if missing, and gather valid parser selections interactively.

**Independent Test**: Launch the wrapper, confirm that `books/` is created if absent, verify supported-file listing, choose options interactively, and confirm the selected values are passed to execution preview.

### Tests for User Story 2

- [x] T015 [P] [US2] Add unit tests for `books/` auto-creation and supported-file discovery in `tests/unit/test_interactive_cli_wrapper.py`
- [x] T016 [P] [US2] Add unit tests for deterministic file listing and path handling with spaces/punctuation in `tests/unit/test_interactive_cli_wrapper.py`
- [x] T017 [P] [US2] Add integration test for empty `books/` behavior in `tests/integration/test_interactive_cli_launcher.py`
- [x] T018 [P] [US2] Add integration test for interactive selection of strategy, config path, output directory, and JSON mode in `tests/integration/test_interactive_cli_launcher.py`

### Implementation for User Story 2

- [x] T019 [US2] Implement `books/` auto-create and supported-file discovery in `src/bookcast_chapter_forge/services/`
- [x] T020 [US2] Implement deterministic interactive file selection in `src/bookcast_chapter_forge/cli/`
- [x] T021 [US2] Implement interactive collection of strategy, config path, output directory, and JSON mode in `src/bookcast_chapter_forge/cli/`
- [x] T022 [US2] Implement pre-execution validation and correctable error handling in `src/bookcast_chapter_forge/cli/`

**Checkpoint**: Source file and core parser options can be selected safely and interactively.

---

## Phase 5: User Story 3 - Preserve The Existing Non-Interactive Parser Path (Priority: P3)

**Goal**: Keep the direct parser CLI unchanged while ensuring the wrapper remains only a convenience layer over the current backend.

**Independent Test**: Verify the direct parser CLI still behaves as before, and verify the interactive wrapper delegates through the existing parser backend rather than duplicating parser logic.

### Tests for User Story 3

- [x] T023 [P] [US3] Add integration test proving the wrapper delegates to the existing parser backend contract in `tests/integration/test_interactive_cli_launcher.py`
- [x] T024 [P] [US3] Re-run and, if needed, extend direct parser CLI regression coverage in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 3

- [x] T025 [US3] Ensure the wrapper uses the existing parser service or CLI entrypoint contract in `src/bookcast_chapter_forge/cli/`
- [x] T026 [US3] Keep the direct parser CLI untouched except for additive integration points in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [x] T027 [US3] Document wrapper/backend contract boundaries in `src/bookcast_chapter_forge/cli/` and `specs/005-interactive-cli-wrapper/contracts/`

**Checkpoint**: The wrapper is additive, and the current parser CLI remains stable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final docs, contracts, and verification for the interactive wrapper.

- [x] T028 [P] Add quickstart examples for `bookcast_forge.sh`, cancellation, and `books/` auto-create behavior in `specs/005-interactive-cli-wrapper/quickstart.md`
- [x] T029 [P] Add research decisions around prompt mechanism and backend delegation in `specs/005-interactive-cli-wrapper/research.md`
- [x] T030 [P] Add interactive wrapper data-model notes in `specs/005-interactive-cli-wrapper/data-model.md`
- [x] T031 Add/update interactive wrapper contracts in `specs/005-interactive-cli-wrapper/contracts/`
- [x] T032 Run full test suite and document closure results in `specs/005-interactive-cli-wrapper/closure.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks user stories
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on US1 completion per feature sequencing
- **Phase 5 (US3)**: Depends on US1 + US2
- **Phase 6 (Polish)**: Depends on completed user stories

### User Story Dependencies

- **US1 (P1)**: First deliverable; introduces the interactive launcher and confirmed execution flow
- **US2 (P2)**: Second deliverable; adds `books/` auto-create, file discovery, and safe option selection
- **US3 (P3)**: Final deliverable; hardens delegation boundaries and preserves the existing direct parser CLI

### Within Each User Story

- Tests must be created and observed failing before implementation
- Wrapper data structures and prompt flow before backend delegation validation
- Backend delegation before documentation-only closure work
- Story validation checkpoint before moving to next priority

### Parallel Opportunities

- Setup tasks T002-T003 can run in parallel
- Foundational tasks T005-T007 can run in parallel where files do not overlap
- Test tasks marked `[P]` within each story can run in parallel
- Different story tasks should not be parallelized across stories due to required `US1 -> US2 -> US3` sequencing

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup + Foundational
2. Deliver the interactive launcher and confirmation flow (`US1`)
3. Validate that the wrapper can launch a confirmed run through the existing parser backend

### Incremental Delivery

1. Deliver `US1` interactive launcher and execution flow
2. Deliver `US2` `books/` auto-create, file discovery, and safe option selection
3. Deliver `US3` additive backend delegation hardening
4. Finish with docs/contracts/research/data-model and closure verification

### Parallel Team Strategy

With multiple developers:

1. One developer can build the wrapper request model and prompt flow tests
2. Another can prepare the launcher script and file-discovery support
3. Backend delegation and docs should begin only after the wrapper contract is stable

---

## Notes

- This feature is additive by constitution and spec: no redesign of parser strategies is planned.
- The main architectural change is the introduction of an interactive launcher over the existing parser backend.
- The `books/` directory should be created automatically if it does not exist.
- The wrapper is intended to improve usability, not replace the current direct parser CLI.
