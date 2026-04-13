# Tasks: Adaptive Strategy Fallback

**Input**: Design documents from `specs/003-adaptive-strategy-fallback/`  
**Prerequisites**: `specs/003-adaptive-strategy-fallback/plan.md` (required), `specs/003-adaptive-strategy-fallback/spec.md` (required for user stories)

**Tests**: Tests are required for this feature because constitution requires test-first work and each user story has independent test criteria.

**Organization**: Tasks are grouped by user story to support independent implementation and validation while preserving the required sequence `US1 -> US2 -> US3`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout at repository root: `src/`, `tests/`, `configs/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare config, docs, and wrapper-facing surfaces needed by the adaptive flow.

- [x] T001 Add adaptive-wrapper documentation and default-usage notes in `README.md`
- [x] T002 [P] Add `adaptive` wrapper configuration section in `configs/config.yaml`
- [x] T003 [P] Add strategy/default-selection notes for adaptive flow in `AGENTS.md` if needed via the normal agent-context update process

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define wrapper decision objects and minimal wiring before story implementation begins.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [x] T004 Add wrapper decision dataclasses (`StrategyAttempt`, `AdaptiveDecision`, `OutputSensibilityReview`) in `src/bookcast_chapter_forge/domain/entities.py`
- [x] T005 [P] Add adaptive-wrapper helper functions for suffix normalization and deterministic acceptance checks in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T006 [P] Extend config loader parsing/validation for adaptive-wrapper keys in `src/bookcast_chapter_forge/services/config_loader.py`
- [x] T007 [P] Add structured logging event names for adaptive attempts, sensibility review, and selected winner in `src/bookcast_chapter_forge/infrastructure/logging.py`

**Checkpoint**: Foundation complete; user stories can now be implemented in planned order.

---

## Phase 3: User Story 1 - Use Adaptive As Default Wrapper (Priority: P1) - MVP

**Goal**: Add a default wrapper path that executes `regex -> layout -> llm` in order and stops at the first accepted result.

**Independent Test**: Run the parser without `--strategy` on a PDF where `regex` fails and `layout` succeeds; verify the wrapper automatically advances and returns the accepted result.

### Tests for User Story 1

> **NOTE: Write these tests FIRST; ensure they fail before implementation.**

- [x] T008 [P] [US1] Add unit tests for adaptive attempt ordering and stop-on-first-accepted-result in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T009 [P] [US1] Add unit tests for continuing after dependency/runtime failure or empty result in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T009a [P] [US1] Add unit test for trying a randomized secondary strategy pool only after `regex -> layout -> llm` runs dry in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T010 [P] [US1] Add integration test for omitted `--strategy` defaulting to adaptive flow in `tests/integration/test_pdf_parser_cli.py`
- [x] T011 [P] [US1] Add integration test for adaptive wrapper orchestration via service/CLI path in `tests/integration/test_pdf_parser_service.py`

### Implementation for User Story 1

- [x] T012 [US1] Implement `adaptive` wrapper orchestration in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T012a [US1] Implement secondary randomized fallback over `index`, `heuristic`, and `semantic` after the primary cascade runs dry in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T013 [US1] Wire omitted `--strategy` to the adaptive wrapper in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [x] T014 [US1] Add adaptive wrapper invocation hooks in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T015 [US1] Emit structured adaptive attempt logs and winner selection logs in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`

**Checkpoint**: US1 is independently functional and the parser can run through the adaptive default path.

---

## Phase 4: User Story 2 - Use An LLM Mind To Judge Output Sensibility (Priority: P2)

**Goal**: Evaluate produced outputs for sensibility before allowing the adaptive wrapper to stop.

**Independent Test**: Run adaptive flow on a case with duplicate normalized output suffixes or fewer than three files and verify the current result is rejected and fallback continues.

### Tests for User Story 2

- [x] T016 [P] [US2] Add unit tests for normalized output suffix uniqueness checks in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T017 [P] [US2] Add unit tests for page-span sanity checks relative to source PDF page count in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T018 [P] [US2] Add unit tests for low-file-count gating and per-file LLM review in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T019 [P] [US2] Add unit tests for LLM-mind rejection causing fallback continuation in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T020 [P] [US2] Add integration test for adaptive rejection of duplicate filenames after numeric prefix removal in `tests/integration/test_pdf_parser_service.py`

### Implementation for User Story 2

- [x] T021 [US2] Implement deterministic sensibility checks for filename uniqueness and page-span sanity in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T022 [US2] Implement bounded LLM-mind review of produced output summaries in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T023 [US2] Continue fallback when sensibility review rejects current output in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T024 [US2] Reuse existing local `llama.cpp` runtime configuration for wrapper-level sensibility review in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`

**Checkpoint**: Adaptive wrapper rejects suspicious outputs and continues fallback when needed.

---

## Phase 5: User Story 3 - Explain Adaptive Decisions (Priority: P3)

**Goal**: Make the adaptive wrapper debuggable through structured diagnostics and clear failures.

**Independent Test**: Run adaptive flow across mixed success/failure paths and verify metadata/warnings identify attempted strategies, rejected outputs, and the winning strategy.

### Tests for User Story 3

- [x] T025 [P] [US3] Add unit tests for structured attempt-path metadata and failure reasons in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T026 [P] [US3] Add unit tests for final winner metadata and rejection rationale capture in `tests/unit/test_adaptive_parser_wrapper.py`
- [x] T027 [P] [US3] Add CLI integration test asserting adaptive diagnostics are surfaced in JSON output mode in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 3

- [x] T028 [US3] Add adaptive decision metadata and warning propagation in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T029 [US3] Ensure clear terminal failure when no fallback step produces acceptable output in `src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py`
- [x] T030 [US3] Document adaptive attempt-path semantics and output diagnostics in `src/bookcast_chapter_forge/cli/pdf_parser.py`

**Checkpoint**: Adaptive wrapper behavior is transparent and diagnosable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final docs, verification, and readiness checks across the wrapper flow.

- [x] T031 [P] Document adaptive default behavior, fallback order, and local `llama-server` requirement in `README.md`
- [x] T032 [P] Add quickstart scenarios for default adaptive runs and explicit strategy override runs in `specs/003-adaptive-strategy-fallback/quickstart.md`
- [x] T033 Add/update wrapper contracts and failure semantics in `specs/003-adaptive-strategy-fallback/contracts/adaptive-wrapper-contract.md`
- [x] T034 [P] Add research decisions and alternatives in `specs/003-adaptive-strategy-fallback/research.md`
- [x] T035 [P] Add wrapper data model notes in `specs/003-adaptive-strategy-fallback/data-model.md`
- [x] T036 Run full test suite and document results for feature closure in `specs/003-adaptive-strategy-fallback/closure.md`

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

- **US1 (P1)**: First deliverable; establishes default adaptive orchestration
- **US2 (P2)**: Second deliverable; adds sensibility review and fallback continuation rules
- **US3 (P3)**: Final wrapper story; adds diagnostics and clearer failure semantics

### Within Each User Story

- Tests must be created and observed failing before implementation
- Wrapper implementation before CLI/service integration validation
- CLI/service integration before documentation-only closure work
- Story validation checkpoint before moving to next priority

### Parallel Opportunities

- Setup tasks T002-T003 can run in parallel
- Foundational tasks T005-T007 can run in parallel where files do not overlap
- Test tasks marked `[P]` within each story can run in parallel
- Different story tasks should not be parallelized across stories due to required `US1 -> US2 -> US3` sequencing

---

## Parallel Example: User Story 2

```bash
# Run US2 tests in parallel:
Task: "Add unit tests for normalized output suffix uniqueness checks in tests/unit/test_adaptive_parser_wrapper.py"
Task: "Add unit tests for page-span sanity checks in tests/unit/test_adaptive_parser_wrapper.py"
Task: "Add unit tests for low-file-count gating and per-file LLM review in tests/unit/test_adaptive_parser_wrapper.py"

# After tests exist, parallelize independent implementations:
Task: "Implement deterministic sensibility checks in src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py"
Task: "Reuse existing llama.cpp runtime configuration for wrapper-level sensibility review in src/bookcast_chapter_forge/services/adaptive_parser_wrapper.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup + Foundational
2. Deliver adaptive wrapper orchestration (`US1`)
3. Validate default no-strategy path and explicit fallback sequence

### Incremental Delivery

1. Deliver `US1` as the default wrapper path
2. Deliver `US2` sensibility review and fallback continuation
3. Deliver `US3` diagnostics and failure transparency
4. Finish with docs/contracts/research/data-model and closure validation

### Parallel Team Strategy

With multiple developers:

1. Pair on wrapper foundation and shared decision objects
2. One developer can finish CLI/service wiring while another prepares sensibility-review tests
3. LLM-mind review work starts only after adaptive wrapper orchestration is stable enough to produce candidate outputs worth judging

---

## Notes

- This feature is additive by constitution and spec: no refactor of existing classifier strategies is planned.
- The wrapper is intentionally above classifier level and should orchestrate parser executions rather than absorb classifier behavior.
- The chosen default path is a primary cascade of `regex -> layout -> llm`.
- If that primary path runs dry, the wrapper uses a secondary randomized pool of `index`, `heuristic`, and `semantic` before failing.
