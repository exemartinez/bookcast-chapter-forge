# Feature Specification: Heuristic Chapter Detection

**Feature Branch**: `002-heuristic-chapter-detection`  
**Created**: 2026-04-08  
**Status**: Draft  
**Input**: User description: "Heuristic PDF chapter detection that improves on feature 001 by evaluating multiple structural signals such as TOC text, page labels, hyperlinks, PDF outlines, layout-aware heading extraction, and optional local-model assistance to choose chapter boundaries more reliably across messy English-language books."

## Scope

Feature 002 is strictly additive. It introduces new chapter-classification strategies only.

- The system MUST keep the current architecture and pipeline shape.
- New logic MUST be implemented as new classes implementing `ChapterClassifier`.
- Existing `fixed`, `regex`, and `index` strategies are out of scope for refactoring.
- Any changes outside strategy registration and classifier-specific dependencies are out of scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Layout-Aware Classifier Variant (Priority: P1)

As a developer, I can select a layout-aware strategy that uses `pymupdf4llm` signals to infer chapter starts from heading hierarchy, typography, spacing, and block segmentation when plain-text parsing is insufficient.

**Why this priority**: This is the first foundational signal source for messy PDFs and should land before the final integrated heuristic strategy.

**Independent Test**: Can be tested independently by invoking the layout-aware strategy on PDFs where heading style is visible in layout structure and validating boundary outputs satisfy `ChapterClassifier` contract constraints.

**Acceptance Scenarios**:

1. **Given** a PDF with weak plain-text TOC but clear visual heading structure, **When** the layout-aware strategy runs, **Then** chapter starts are inferred from layout evidence and valid chunks are returned.
2. **Given** `pymupdf4llm` is not available, **When** the layout-aware strategy is selected, **Then** the system fails with a clear strategy-specific dependency error instead of affecting other strategies.

---

### User Story 2 - Add Semantic Section Variant (Priority: P2)

As a developer, I can select a semantic section strategy using `unstructured` to infer likely chapter boundaries from title-like section transitions when plain-text and layout-only approaches are not enough.

**Why this priority**: This adds a second non-TOC signal source for difficult PDFs without yet introducing local-model runtime complexity.

**Independent Test**: Can be tested by running the semantic strategy on known ambiguous PDFs and verifying it remains optional, selectable, and contract-compliant without changing other classifiers.

**Acceptance Scenarios**:

1. **Given** a PDF with unreliable TOC but recognizable section titles, **When** the semantic strategy runs, **Then** boundaries are inferred from title/section transitions and valid chunks are returned.
2. **Given** `unstructured` is not available, **When** the semantic strategy is selected, **Then** the system fails with a clear strategy-specific dependency error instead of affecting other strategies.

---

### User Story 3 - Add Hybrid Heuristic Integrator Classifier (Priority: P3)

As a developer using the parser service or CLI, I can select a new `heuristic` strategy that integrates evidence from the layout-aware and semantic approaches (plus TOC text, page labels, hyperlinks, and outlines) to produce stronger final chapter-boundary decisions through the existing classifier contract.

**Why this priority**: This is the final integration story and should be implemented last, after foundational signal-producing strategies are available.

**Independent Test**: Can be tested by running the parser with `--strategy heuristic` on representative PDFs after User Stories 1 and 2 are implemented, verifying integrated evidence produces valid chunk boundaries and output files through the unchanged service/writer flow.

**Acceptance Scenarios**:

1. **Given** layout-aware and semantic evidence are available for a PDF, **When** the `heuristic` strategy runs, **Then** it combines corroborated signals and returns valid non-overlapping chunks in `ClassificationResult`.
2. **Given** weak or conflicting evidence from one source, **When** the `heuristic` strategy runs, **Then** it uses deterministic tie-break rules over combined signals and still returns valid chunks.
3. **Given** a caller uses existing parser orchestration, **When** `heuristic` is selected, **Then** no service-layer API changes are required.

---

### User Story 4 - Add Large Language Model Enhancer (Priority: P4)

As a developer, I can select a local-LLM-enhanced strategy that starts from the `layout` classifier result and uses a lightweight local model to validate whether each proposed cut is correct and whether the output filename/title is the right one.

**Why this priority**: The heuristics in feature 001 and the early 002 strategies are good enough to generate candidates, but some PDFs require a human-like judgment pass over local evidence to decide whether a cut is valid or mislabeled.

**Independent Test**: Can be tested independently by running the LLM-enhanced strategy on PDFs where `layout` finds plausible chapter starts but front matter or TOC pages are easily confused with real chapters, and verifying the model keeps or rejects cuts and adjusts titles using only structured local evidence.

**Acceptance Scenarios**:

1. **Given** a PDF where the `layout` strategy proposes candidate chapter cuts, **When** the LLM enhancer runs, **Then** it re-evaluates each proposed cut using local structured evidence around the candidate pages and either confirms or rejects the cut.
2. **Given** a proposed chunk title or filename that does not match the visible heading of the selected section, **When** the LLM enhancer runs, **Then** it returns a corrected canonical title for that chunk.
3. **Given** `llama-server` or the selected local model is unavailable, **When** the LLM enhancer is selected, **Then** the system fails with a clear strategy-specific dependency/runtime error instead of affecting other strategies.
4. **Given** the local model is available, **When** the LLM enhancer runs, **Then** it uses a local `llama.cpp` `llama-server` OpenAI-compatible endpoint with a lightweight default model and consumes structured evidence rather than the full PDF text.

### Edge Cases

- PDFs with missing or contradictory TOC text, page labels, outline metadata, and heading typography.
- PDFs with extractable text but noisy segmentation, causing repeated false heading candidates.
- PDFs where no strategy-specific signal is strong enough to create confident multi-chunk output.
- Optional dependencies (`pymupdf4llm`, `unstructured`, local model stack) unavailable at runtime.
- Documents with front/back matter that resemble chapters and can trigger false boundaries.
- Layout-detected cuts whose heading text is correct but whose surrounding pages show the cut actually belongs to preface, TOC, or appendix material.
- Layout-detected cuts whose extracted title is too generic, repeated, truncated, or otherwise unsafe to use as the final output filename.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a new `heuristic` classifier strategy that implements `ChapterClassifier` and combines multiple structural signals to infer chapter boundaries.
- **FR-002**: System MUST keep existing strategies (`fixed`, `regex`, `index`) behaviorally unchanged for this feature scope.
- **FR-003**: System MUST register each new strategy as independently selectable alongside existing strategies.
- **FR-004**: System MUST add a layout-aware classifier strategy that may use `pymupdf4llm` and still returns standard `ClassificationResult` outputs.
- **FR-005**: System MUST add a semantic section classifier strategy that may use `unstructured` and still returns standard `ClassificationResult` outputs.
- **FR-006**: System MUST support an optional model-assisted classifier mode that uses LangChain and/or LangGraph with a local model runtime to disambiguate candidate boundaries.
- **FR-007**: System MUST add a new LLM-enhanced classifier strategy that uses the `layout` strategy as its candidate generator and performs a second-pass validation over proposed cuts and titles.
- **FR-008**: The LLM-enhanced strategy MUST use a local `llama.cpp` `llama-server` OpenAI-compatible endpoint with a lightweight model profile for MVP planning.
- **FR-009**: Model-assisted logic and the LLM enhancer MUST consume structured candidate evidence rather than raw full-document text as direct model input.
- **FR-010**: The LLM enhancer MUST be able to confirm or reject proposed layout cuts and MUST be able to correct the chunk title/filename when local evidence indicates the original label is wrong.
- **FR-011**: Strategy-specific dependency failures MUST surface clear, isolated errors and MUST NOT break unrelated strategies.
- **FR-012**: Feature implementation MUST avoid pipeline redesign and limit non-classifier changes to strategy registration and minimal glue required for selection.
- **FR-013**: Each new classifier strategy MUST be testable independently at unit and integration levels.

### Key Entities *(include if feature involves data)*

- **SignalEvidence**: Strategy-specific extracted indicators (e.g., TOC entries, outline nodes, page labels, heading blocks) used to score candidate chapter starts.
- **BoundaryCandidate**: Proposed chapter boundary with source signals, confidence score, and tie-break metadata.
- **BoundaryDecision**: Final selected ordered boundaries transformed into `ChapterChunk` values returned via `ClassificationResult`.
- **LLMReviewPacket**: Structured local evidence derived from a `layout`-proposed cut, including candidate start/end pages, nearby headings, nearby page snippets, and current proposed title/filename.
- **LLMReviewDecision**: The local model's structured response indicating whether to keep or reject a cut, what title to use, and a short rationale.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least one new strategy (`heuristic`) is available via normal strategy selection and produces valid chunk outputs end-to-end.
- **SC-001a**: A separate LLM-enhanced strategy is available via normal strategy selection and can validate `layout`-produced cuts using a local `llama-server` runtime.
- **SC-002**: Existing `fixed`, `regex`, and `index` strategy tests continue to pass without required behavior changes.
- **SC-003**: New strategy-specific tests cover successful classification and dependency-missing/error paths for optional variants.
- **SC-004**: On the curated evaluation set for feature 002, `heuristic` reduces obvious boundary failures compared to feature 001 baselines as defined in plan/testing docs.
- **SC-005**: On PDFs where `layout` confuses front matter or TOC pages with true chapters, the LLM-enhanced strategy reduces visibly wrong cuts or wrong output titles compared to `layout` alone.

## Assumptions

- Feature 002 targets English-language PDFs only; multilingual robustness is out of scope.
- Optional strategy dependencies may be installed selectively and should not be global hard requirements for all runs.
- Local model assistance is experimental and constrained to structured candidate review, cut validation, and title correction, not full autonomous parsing.
- The local LLM runtime for MVP planning is `llama.cpp` `llama-server`, and the default lightweight model profile is `ggml-org/gemma-3-1b-it-GGUF`.
- CLI/service contracts remain stable; callers only need strategy selection changes to use new classifiers.
