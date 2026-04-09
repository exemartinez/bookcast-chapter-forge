# Tasks: Heuristic Chapter Detection

**Input**: Design documents from `specs/002-heuristic-chapter-detection/`  
**Prerequisites**: `specs/002-heuristic-chapter-detection/plan.md` (required), `specs/002-heuristic-chapter-detection/spec.md` (required for user stories)

**Tests**: Tests are required for this feature because constitution requires test-first work and each user story has independent test criteria.

**Organization**: Tasks are grouped by user story to support independent implementation and validation while preserving the required sequence `US1 -> US2 -> US3 -> US4`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`, `US4`)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout at repository root: `src/`, `tests/`, `configs/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare optional dependency wiring and shared config surfaces needed by all new strategies.

- [x] T001 Add optional dependency groups/documentation for `pymupdf4llm`, `unstructured`, `llama.cpp` integration, and lightweight GGUF model setup in `requirements.txt` and `README.md`
- [x] T002 [P] Extend strategy configuration sections for `layout`, `semantic`, and `heuristic` in `configs/config.yaml`
- [x] T003 [P] Extend strategy configuration sections for `llm` review settings (`provider`, `model`, base_url`, `chat endpoint`, timeouts, review window, prompt controls) in `configs/config.yaml`
- [x] T004 [P] Add strategy-name constants and export updates for implemented strategies in `src/bookcast_chapter_forge/classifiers/__init__.py`
- [x] T005 [P] Add shared fixture placeholders for messy-layout and sectioned PDFs in `tests/fixtures/pdfs/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared evidence/review structures and registration plumbing that all stories depend on.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [x] T006 Add evidence and boundary decision dataclasses (`SignalEvidence`, `BoundaryCandidate`, `BoundaryDecision`) in `src/bookcast_chapter_forge/domain/entities.py`
- [x] T007 Add `LLMReviewPacket` and `LLMReviewDecision` data structures in `src/bookcast_chapter_forge/domain/entities.py`
- [x] T008 [P] Add classifier utility helpers for chunk invariant validation and deterministic sorting in `src/bookcast_chapter_forge/classifiers/utils.py`
- [x] T009 [P] Extend config loader parsing/validation for `layout`, `semantic`, and `heuristic` keys in `src/bookcast_chapter_forge/services/config_loader.py`
- [x] T010 [P] Extend config loader parsing/validation for `llm` strategy keys in `src/bookcast_chapter_forge/services/config_loader.py`
- [x] T011 Register implemented strategy keys (`layout`, `semantic`, `heuristic`) in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T012 Register `llm` strategy key in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T013 [P] Extend CLI strategy choices and help text for implemented strategies in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [x] T014 [P] Extend CLI strategy choices and help text for `llm` strategy in `src/bookcast_chapter_forge/cli/pdf_parser.py`
- [x] T015 [P] Add structured logging event names for evidence extraction, review packets, and boundary decisions in `src/bookcast_chapter_forge/infrastructure/logging.py`

**Checkpoint**: Foundation complete; user stories can now be implemented in planned order.

---

## Phase 3: User Story 1 - Layout-Aware Classifier Variant (Priority: P1) - MVP

**Goal**: Add a selectable `layout` strategy that infers chapter starts using layout-aware signals from `pymupdf4llm` while preserving existing classifier contract.

**Independent Test**: Run parser with `--strategy layout` on a fixture with clear heading typography; verify valid, non-overlapping chunks and strategy-specific missing-dependency error behavior.

### Tests for User Story 1

> **NOTE: Write these tests FIRST; ensure they fail before implementation.**

- [x] T016 [P] [US1] Add unit tests for layout evidence extraction and heading hierarchy scoring in `tests/unit/test_layout_aware_classifier.py`
- [x] T017 [P] [US1] Add unit test for missing `pymupdf4llm` dependency error isolation in `tests/unit/test_layout_aware_classifier.py`
- [x] T018 [P] [US1] Add integration test for `layout` strategy via service pipeline in `tests/integration/test_pdf_parser_service.py`
- [x] T019 [P] [US1] Add CLI integration test for `--strategy layout` in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 1

- [x] T020 [US1] Implement `LayoutAwareClassifier` in `src/bookcast_chapter_forge/classifiers/layout_aware_classifier.py`
- [x] T021 [US1] Add lazy optional import and strategy-local error handling for `pymupdf4llm` in `src/bookcast_chapter_forge/classifiers/layout_aware_classifier.py`
- [x] T022 [US1] Integrate layout strategy registration in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T023 [US1] Emit structured logs for layout evidence and final decisions in `src/bookcast_chapter_forge/classifiers/layout_aware_classifier.py`

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Semantic Section Classifier Variant (Priority: P2)

**Goal**: Add selectable `semantic` strategy using `unstructured` section/title elements without changing the baseline strategies.

**Independent Test**: Run `--strategy semantic` on ambiguous fixtures; verify contract-compliant chunks and strategy-local dependency failures without impact to other strategies.

### Tests for User Story 2

- [x] T024 [P] [US2] Add unit tests for section/title boundary inference in `tests/unit/test_semantic_section_classifier.py`
- [x] T025 [P] [US2] Add unit tests for semantic dependency-missing failure isolation in `tests/unit/test_semantic_section_classifier.py`
- [x] T026 [P] [US2] Add integration test for `semantic` strategy pipeline behavior in `tests/integration/test_pdf_parser_service.py`
- [x] T027 [P] [US2] Add CLI integration test for `--strategy semantic` in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 2

- [x] T028 [US2] Implement `SemanticSectionClassifier` in `src/bookcast_chapter_forge/classifiers/semantic_section_classifier.py`
- [x] T029 [US2] Add lazy optional import and isolated error handling for `unstructured` in `src/bookcast_chapter_forge/classifiers/semantic_section_classifier.py`
- [x] T030 [US2] Register `semantic` strategy in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T031 [US2] Add strategy-specific config parsing and validation for semantic settings in `src/bookcast_chapter_forge/services/config_loader.py`

**Checkpoint**: US1 and US2 are independently functional; optional dependency failures are isolated.

---

## Phase 5: User Story 3 - Hybrid Heuristic Integrator Classifier (Priority: P3)

**Goal**: Add final deterministic `heuristic` strategy that integrates corroborated evidence from layout-aware + semantic paths plus TOC/page-label/hyperlink/outline cues.

**Independent Test**: Run `--strategy heuristic` on representative messy PDFs after US1/US2 are available; verify deterministic tie-break behavior, valid chunks, and no service API changes.

### Tests for User Story 3

- [x] T032 [P] [US3] Add unit tests for multi-signal candidate scoring and deterministic tie-breakers in `tests/unit/test_heuristic_integrator_classifier.py`
- [x] T033 [P] [US3] Add unit tests for non-overlapping ordered chunk generation bounds in `tests/unit/test_heuristic_integrator_classifier.py`
- [x] T034 [P] [US3] Add integration test proving heuristic integration of layout + semantic evidence in `tests/integration/test_pdf_parser_service.py`
- [x] T035 [P] [US3] Add CLI integration test for `--strategy heuristic` in `tests/integration/test_pdf_parser_cli.py`
- [x] T036 [P] [US3] Add regression tests confirming `fixed|regex|index` unchanged behavior in `tests/unit/test_fixed_page_classifier.py`, `tests/unit/test_regex_chapter_classifier.py`, and `tests/unit/test_index_chapter_classifier.py`

### Implementation for User Story 3

- [x] T037 [US3] Implement `HeuristicIntegratorClassifier` in `src/bookcast_chapter_forge/classifiers/heuristic_integrator_classifier.py`
- [x] T038 [US3] Implement deterministic signal precedence and tie-break policy in `src/bookcast_chapter_forge/classifiers/heuristic_integrator_classifier.py`
- [x] T039 [US3] Add integration hooks to consume evidence from layout/semantic outputs in `src/bookcast_chapter_forge/classifiers/heuristic_integrator_classifier.py`
- [x] T040 [US3] Register `heuristic` strategy in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T041 [US3] Add strategy metadata/warnings propagation for confidence diagnostics in `src/bookcast_chapter_forge/services/pdf_parser_service.py`

**Checkpoint**: Deterministic `heuristic` strategy is functional and integrates US1/US2 outputs.

---

## Phase 6: User Story 4 - Large Language Model Enhancer (Priority: P4)

**Goal**: Add an `llm` strategy that starts from `layout`-generated candidates and uses local `llama.cpp` `llama-server` to confirm/reject cuts and correct chunk titles/filenames.

**Independent Test**: Run `--strategy llm` on PDFs where `layout` confuses front matter or TOC pages with real chapters; verify the local model reviews structured packets, rejects bad cuts, and corrects titles without consuming full-document prompts.

### Tests for User Story 4

- [x] T042 [P] [US4] Add unit tests for `LLMReviewPacket` construction from layout-derived cuts in `tests/unit/test_llm_enhanced_classifier.py`
- [x] T043 [P] [US4] Add unit tests for `llama-server` runtime unavailable and model-missing failures in `tests/unit/test_llm_enhanced_classifier.py`
- [x] T044 [P] [US4] Add unit tests proving the LLM enhancer consumes structured local evidence rather than raw full-document text in `tests/unit/test_llm_enhanced_classifier.py`
- [x] T045 [P] [US4] Add integration test for `llm` strategy pipeline behavior in `tests/integration/test_pdf_parser_service.py`
- [x] T046 [P] [US4] Add CLI integration test for `--strategy llm` in `tests/integration/test_pdf_parser_cli.py`

### Implementation for User Story 4

- [x] T047 [US4] Implement `LLMEnhancedClassifier` in `src/bookcast_chapter_forge/classifiers/llm_enhanced_classifier.py`
- [x] T048 [US4] Use `LayoutAwareClassifier` as the sole candidate generator inside `src/bookcast_chapter_forge/classifiers/llm_enhanced_classifier.py`
- [x] T049 [US4] Add OpenAI-compatible `llama-server` adapter and lightweight GGUF default model profile in `src/bookcast_chapter_forge/classifiers/llm_enhanced_classifier.py`
- [x] T050 [US4] Implement structured prompt/response contract that can keep/reject cuts and correct titles in `src/bookcast_chapter_forge/classifiers/llm_enhanced_classifier.py`
- [x] T051 [US4] Register `llm` strategy in `src/bookcast_chapter_forge/services/pdf_parser_service.py`
- [x] T052 [US4] Add strategy-specific config parsing and validation for `llm` settings in `src/bookcast_chapter_forge/services/config_loader.py`

**Checkpoint**: `llm` strategy is functional, optional, and scoped as a second-pass reviewer over `layout`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final docs, verification, and readiness checks across all strategies.

- [x] T053 [P] Document new strategies, optional dependencies, `llama-server` setup, and selection guidance in `README.md`
- [x] T054 [P] Add quickstart scenarios for baseline vs optional strategy runs in `specs/002-heuristic-chapter-detection/quickstart.md`
- [x] T055 Add/update strategy contracts and failure semantics in `specs/002-heuristic-chapter-detection/contracts/chapter-classification-contract.md`
- [x] T056 [P] Add research decisions and alternatives in `specs/002-heuristic-chapter-detection/research.md`
- [x] T057 [P] Add entity/evidence/review model notes in `specs/002-heuristic-chapter-detection/data-model.md`
- [x] T058 Run full test suite and document results for feature closure in `specs/002-heuristic-chapter-detection/closure.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks user stories
- **Phase 3 (US1)**: Depends on Phase 2
- **Phase 4 (US2)**: Depends on US1 completion per feature sequencing
- **Phase 5 (US3)**: Depends on US1 + US2
- **Phase 6 (US4)**: Depends on US1 and should begin only after deterministic strategies are stable
- **Phase 7 (Polish)**: Depends on completed user stories

### User Story Dependencies

- **US1 (P1)**: First deliverable; foundation for later signal integration
- **US2 (P2)**: Second deliverable; adds semantic evidence source
- **US3 (P3)**: Deterministic integrator story; combines US1 + US2 evidence into `heuristic`
- **US4 (P4)**: LLM review story; depends on `layout` and should be implemented after deterministic baseline behavior is understood

### Within Each User Story

- Tests must be created and observed failing before implementation
- Classifier module implementation before service registration
- Service registration before CLI integration validation
- Story validation checkpoint before moving to next priority

### Parallel Opportunities

- Setup tasks T002-T005 can run in parallel
- Foundational tasks T008-T015 can run in parallel where files do not overlap
- Test tasks marked `[P]` within each story can run in parallel
- Different story tasks should not be parallelized across stories due to required `US1 -> US2 -> US3 -> US4` sequencing

---

## Parallel Example: User Story 4

```bash
# Run US4 tests in parallel:
Task: "Add unit tests for LLMReviewPacket construction in tests/unit/test_llm_enhanced_classifier.py"
Task: "Add unit tests for Ollama runtime failure behavior in tests/unit/test_llm_enhanced_classifier.py"
Task: "Add integration test for llm strategy in tests/integration/test_pdf_parser_service.py"

# After tests exist, parallelize independent implementations:
Task: "Implement LLMEnhancedClassifier in src/bookcast_chapter_forge/classifiers/llm_enhanced_classifier.py"
Task: "Add llm strategy config parsing in src/bookcast_chapter_forge/services/config_loader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup + Foundational
2. Deliver layout-aware strategy (`US1`)
3. Validate independently and keep existing strategies stable

### Incremental Delivery

1. Deliver `US1` (`layout`) as first improvement slice
2. Deliver `US2` (`semantic`) as second slice
3. Deliver `US3` (`heuristic`) as deterministic combined strategy
4. Deliver `US4` (`llm`) as a local-review enhancement over `layout`
5. Finish with docs/contracts/research/data-model and closure validation

### Parallel Team Strategy

With multiple developers:

1. Pair on Foundational tasks and shared interfaces
2. One developer can finish remaining deterministic tests while another prepares Ollama-specific scaffolding after US3 is stable
3. LLM enhancer work (US4) starts only after `layout` is reliable enough to provide candidate cuts worth reviewing

---

## Notes

- This feature is additive by constitution and spec: no refactor of existing baseline strategies is planned.
- Optional dependencies must remain isolated and never break baseline parser functionality.
- `heuristic` is intentionally the last deterministic strategy because it integrates prior deterministic story outputs.
- `llm` is intentionally a reviewer over `layout`, not a replacement parser and not a full-document prompting workflow.
