# Tasks: Heuristic Chapter Detection

**Input**: Design documents from `specs/002-heuristic-chapter-detection/`  
**Prerequisites**: `specs/002-heuristic-chapter-detection/plan.md` (required), `specs/002-heuristic-chapter-detection/spec.md` (required for user stories)

**Tests**: Tests are required for this feature because constitution requires test-first work and each user story has independent test criteria.

**Organization**: Tasks are grouped by user story to support independent implementation and validation while preserving the required sequence `US1 -> US2 -> US3`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout at repository root: `src/`, `tests/`, `configs/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare optional dependency wiring and shared config surfaces needed by all new strategies.

- [ ] T001 Add optional dependency groups/documentation for `pymupdf4llm`, `unstructured`, `langchain`/`langgraph` in `requirements.txt` and `README.md`
- [ ] T002 [P] Extend strategy configuration sections for `layout`, `semantic`, `model`, and `heuristic` in `configs/config.yaml`
- [x] T003 [P] Add strategy-name constants and export updates in `src/bookcast_chapter_forge/classifiers/__init__.py`
- [ ] T004 [P] Add shared fixture placeholders for messy-layout and sectioned PDFs in `tests/fixtures/pdfs/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared evidence/decision structures and registration plumbing that all stories depend on.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [ ] T005 Add evidence and boundary decision dataclasses (`SignalEvidence`, `BoundaryCandidate`, `BoundaryDecision`) in `src/bookcast_chapter_forge/domain/entities.py`
- [x] T006 [P] Add classifier utility helpers for chunk invariant validation and deterministic sorting in `src/bookcast_chapter_forge/classifiers/utils.py`
- [ ] T007 [P] Extend config loader parsing/validation for new strategy keys in `src/bookcast_chapter_forge/services/config_loader.py`
- [x] T008 Register new strategy keys (`layout`, `semantic`, `model`, `heuristic`) in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T009 [P] Extend CLI strategy choices and help text for new strategies in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [ ] T010 [P] Add structured logging event names for evidence extraction and boundary decisions in `src/bookcast_chapter_forge/infrastructure/logging.py`

**Checkpoint**: Foundation complete; user stories can now be implemented in planned order.

---

## Phase 3: User Story 1 - Layout-Aware Classifier Variant (Priority: P1) - MVP

**Goal**: Add a selectable `layout` strategy that infers chapter starts using layout-aware signals from `pymupdf4llm` while preserving existing classifier contract.

**Independent Test**: Run parser with `--strategy layout` on a fixture with clear heading typography; verify valid, non-overlapping chunks and strategy-specific missing-dependency error behavior.

### Tests for User Story 1 

> **NOTE: Write these tests FIRST; ensure they fail before implementation.**

- [ ] T011 [P] [US1] Add unit tests for layout evidence extraction and heading hierarchy scoring in `tests/unit/test_layout_aware_classifier.py`
- [x] T012 [P] [US1] Add unit test for missing `pymupdf4llm` dependency error isolation in `tests/unit/test_layout_aware_classifier.py`
- [ ] T013 [P] [US1] Add integration test for `layout` strategy via service pipeline in `tests/integration/test_pdf_parser_service.py`
- [x] T014 [P] [US1] Add CLI integration test for `--strategy layout` in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `LayoutAwareClassifier` in `src/bookcast_chapter_forge/classifiers/layout_aware_classifier.py`
- [x] T016 [US1] Add lazy optional import and strategy-local error handling for `pymupdf4llm` in `src/bookcast_chapter_forge/classifiers/layout_aware_classifier.py`
- [x] T017 [US1] Integrate layout strategy registration in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [ ] T018 [US1] Emit structured logs for layout evidence and final decisions in `src/bookcast_chapter_forge/classifiers/layout_aware_classifier.py`

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Semantic and Optional Model-Assisted Variants (Priority: P2)

**Goal**: Add selectable `semantic` strategy (via `unstructured`) and optional `model` strategy (LangChain/LangGraph + local runtime) for ambiguous-boundary ranking from structured evidence.

**Independent Test**: Run `--strategy semantic` and `--strategy model` on ambiguous fixtures; verify contract-compliant chunks and strategy-local dependency failures without impact to other strategies.

### Tests for User Story 2 

- [ ] T019 [P] [US2] Add unit tests for section/title boundary inference in `tests/unit/test_semantic_section_classifier.py`
- [x] T020 [P] [US2] Add unit tests for semantic dependency-missing failure isolation in `tests/unit/test_semantic_section_classifier.py`
- [ ] T021 [P] [US2] Add unit tests proving model-assisted mode consumes structured candidates (not raw full text) in `tests/unit/test_model_assisted_classifier.py`
- [x] T022 [P] [US2] Add unit tests for model-runtime unavailable errors in `tests/unit/test_model_assisted_classifier.py`
- [ ] T023 [P] [US2] Add integration test for `semantic` strategy pipeline behavior in `tests/integration/test_pdf_parser_service.py`
- [x] T024 [P] [US2] Add CLI integration tests for `--strategy semantic` and `--strategy model` in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `SemanticSectionClassifier` in `src/bookcast_chapter_forge/classifiers/semantic_section_classifier.py`
- [x] T026 [US2] Add lazy optional import and isolated error handling for `unstructured` in `src/bookcast_chapter_forge/classifiers/semantic_section_classifier.py`
- [ ] T027 [US2] Implement `ModelAssistedClassifier` with structured-candidate ranking pipeline in `src/bookcast_chapter_forge/classifiers/model_assisted_classifier.py`
- [ ] T028 [US2] Add optional LangChain/LangGraph + local model runtime adapter in `src/bookcast_chapter_forge/classifiers/model_assisted_classifier.py`
- [x] T029 [US2] Register `semantic` and `model` strategies in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [ ] T030 [US2] Add strategy-specific config parsing and validation for semantic/model settings in `src/bookcast_chapter_forge/services/config_loader.py`

**Checkpoint**: US1 and US2 are independently functional; optional dependency failures are isolated.

---

## Phase 5: User Story 3 - Hybrid Heuristic Integrator Classifier (Priority: P3)

**Goal**: Add final `heuristic` strategy that integrates corroborated evidence from layout-aware + semantic/model-assisted paths plus TOC/page-label/hyperlink/outline cues.

**Independent Test**: Run `--strategy heuristic` on representative messy PDFs after US1/US2 are available; verify deterministic tie-break behavior, valid chunks, and no service API changes.

### Tests for User Story 3 

- [ ] T031 [P] [US3] Add unit tests for multi-signal candidate scoring and deterministic tie-breakers in `tests/unit/test_heuristic_integrator_classifier.py`
- [ ] T032 [P] [US3] Add unit tests for non-overlapping ordered chunk generation bounds in `tests/unit/test_heuristic_integrator_classifier.py`
- [ ] T033 [P] [US3] Add integration test proving heuristic integration of layout + semantic evidence in `tests/integration/test_pdf_parser_service.py`
- [x] T034 [P] [US3] Add CLI integration test for `--strategy heuristic` in `tests/integration/test_pdf_parser_cli.py`
- [ ] T035 [P] [US3] Add regression tests confirming `fixed|regex|index` unchanged behavior in `tests/unit/test_fixed_page_classifier.py`, `tests/unit/test_regex_chapter_classifier.py`, and `tests/unit/test_index_chapter_classifier.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `HeuristicIntegratorClassifier` in `src/bookcast_chapter_forge/classifiers/heuristic_integrator_classifier.py`
- [ ] T037 [US3] Implement deterministic signal precedence and tie-break policy in `src/bookcast_chapter_forge/classifiers/heuristic_integrator_classifier.py`
- [ ] T038 [US3] Add integration hooks to consume evidence from layout/semantic/model outputs in `src/bookcast_chapter_forge/classifiers/heuristic_integrator_classifier.py`
- [x] T039 [US3] Register `heuristic` strategy in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [ ] T040 [US3] Add strategy metadata/warnings propagation for confidence diagnostics in `src/bookcast_chapter_forge/services/pdf_parser_service.py`

**Checkpoint**: All user stories are functional; hybrid strategy is implemented last and integrates US1/US2 outputs.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final docs, verification, and readiness checks across all strategies.

- [ ] T041 [P] Document new strategies, optional dependencies, and selection guidance in `README.md`
- [ ] T042 [P] Add quickstart scenarios for baseline vs optional strategy runs in `specs/002-heuristic-chapter-detection/quickstart.md`
- [ ] T043 Add/update strategy contracts and failure semantics in `specs/002-heuristic-chapter-detection/contracts/chapter-classification-contract.md`
- [ ] T044 [P] Add research decisions and alternatives in `specs/002-heuristic-chapter-detection/research.md`
- [ ] T045 [P] Add entity/evidence model notes in `specs/002-heuristic-chapter-detection/data-model.md`
- [ ] T046 Run full test suite and document results for feature closure in `specs/002-heuristic-chapter-detection/closure.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks user stories
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on US1 completion per feature sequencing
- **Phase 5 (US3)**: Depends on US1 + US2; must be implemented last
- **Phase 6 (Polish)**: Depends on completed user stories

### User Story Dependencies

- **US1 (P1)**: First deliverable; foundation for later signal integration
- **US2 (P2)**: Second deliverable; adds semantic/model evidence sources
- **US3 (P3)**: Final integrator story; combines US1 + US2 evidence into `heuristic`

### Within Each User Story

- Tests must be created and observed failing before implementation
- Classifier module implementation before service registration
- Service registration before CLI integration validation
- Story validation checkpoint before moving to next priority

### Parallel Opportunities

- Setup tasks T002-T004 can run in parallel
- Foundational tasks T006, T007, T009, T010 can run in parallel
- Test tasks marked `[P]` within each story can run in parallel
- Different story tasks should not be parallelized across stories due to required US1 -> US2 -> US3 sequencing

---

## Parallel Example: User Story 2

```bash
# Run US2 tests in parallel:
Task: "Add unit tests for section/title boundary inference in tests/unit/test_semantic_section_classifier.py"
Task: "Add unit tests for model-assisted structured-candidate usage in tests/unit/test_model_assisted_classifier.py"
Task: "Add integration test for semantic strategy in tests/integration/test_pdf_parser_service.py"

# After tests exist, parallelize independent implementations:
Task: "Implement SemanticSectionClassifier in src/bookcast_chapter_forge/classifiers/semantic_section_classifier.py"
Task: "Implement ModelAssistedClassifier in src/bookcast_chapter_forge/classifiers/model_assisted_classifier.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup + Foundational
2. Deliver layout-aware strategy (`US1`)
3. Validate independently and keep existing strategies stable

### Incremental Delivery

1. Deliver `US1` (`layout`) as first improvement slice
2. Deliver `US2` (`semantic` + optional `model`) as second slice
3. Deliver `US3` (`heuristic` integrator) as final combined strategy
4. Finish with docs/contracts/research/data-model and closure validation

### Parallel Team Strategy

With multiple developers:

1. Pair on Foundational tasks and shared interfaces
2. One developer leads semantic strategy while another leads model strategy during US2
3. Integrator work (US3) starts only after both US1 and US2 are merged and stable

---

## Notes

- This feature is additive by constitution and spec: no refactor of existing strategies is planned.
- Optional dependencies must remain isolated and never break baseline parser functionality.
- `heuristic` strategy is intentionally sequenced as the last story because it integrates prior story outputs.
