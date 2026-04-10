# Implementation Plan: Adaptive Strategy Fallback

**Branch**: `003-adaptive-strategy-fallback` | **Date**: 2026-04-10 | **Spec**: `specs/003-adaptive-strategy-fallback/spec.md`  
**Input**: Feature specification from `specs/003-adaptive-strategy-fallback/spec.md`

## Summary

Add one new adaptive wrapper flow over the existing parser entrypoint in `src/bookcast_chapter_forge/cli/pdf_parser.py`. The wrapper becomes the default parser path when no explicit strategy is provided, executes a deterministic fallback cascade of `regex -> layout -> llm`, evaluates each produced result with an LLM mind plus deterministic sanity checks, and either stops at the first sensible result or continues to the next fallback step. Existing classifier strategies remain unchanged and independently selectable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Existing: `pypdf`, `PyYAML`, `pytest`; feature reuses existing parser service and `llama.cpp` `llama-server` integration from feature 002  
**Storage**: Local filesystem only (`books/`, `configs/`, `output/`)  
**Testing**: `pytest`, `pytest-cov` (unit + integration; slow markers remain reserved for larger real-book scenarios)  
**Target Platform**: macOS/Linux CLI environment  
**Project Type**: Single-package CLI application  
**Performance Goals**: Keep the wrapper practical for local CLI usage by limiting fallback steps and bounding LLM review payloads  
**Constraints**: Additive-only wrapper over existing parser flow, no behavioral refactor of existing strategies, offline-first defaults, deterministic fallback order, structured diagnostics, bounded local-model review  
**Scale/Scope**: Feature-local orchestration for English-language PDFs; no architecture rewrite; no new application surface beyond the existing CLI/service flow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- OO-first modularity: Pass. The feature adds one orchestration component rather than spreading fallback logic across existing classifiers.
- CLI-first interface: Pass. The existing parser CLI remains the primary entry point, and the wrapper integrates there.
- Test-first workflow: Pass. Wrapper behavior, fallback order, and sensibility-review rules are test-defined before implementation.
- Observability: Pass. The wrapper must emit structured attempt-path and winner diagnostics.
- Simplicity and additive evolution: Pass. Existing strategies remain intact; only wrapper logic and default selection are added.
- Strategy isolation (VIII): Pass. Existing classifiers remain unchanged and independently selectable.
- Contract/data integrity (IX): Pass. Wrapper accepts or rejects complete parser results using existing chunk invariants.
- Determinism (X): Pass with bounded exception for the local-model sensibility review.
- Dependency discipline (XI): Pass. Local-model review reuses existing optional runtime behavior and remains isolated.
- Security/privacy (XII): Pass. The local model reviews structured output metadata and bounded local evidence only.

No constitution violations are required for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/003-adaptive-strategy-fallback/
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
    │   ├── pdf_parser_service.py
    │   └── adaptive_parser_wrapper.py     # new
    ├── classifiers/
    │   ├── base.py
    │   ├── fixed_page_classifier.py
    │   ├── regex_chapter_classifier.py
    │   ├── index_chapter_classifier.py
    │   ├── layout_aware_classifier.py
    │   ├── semantic_section_classifier.py
    │   ├── heuristic_integrator_classifier.py
    │   └── llm_enhanced_classifier.py
    └── infrastructure/
        └── logging.py

configs/
└── config.yaml

tests/
├── unit/
└── integration/
```

**Structure Decision**: Keep the existing single-package CLI architecture. Add one wrapper/orchestration component under `services/` and minimal CLI/service/config glue only. Do not implement feature 003 as a new classifier.

## Implementation Design

### Core Wrapper Behavior

- Reuse the existing parser entrypoint and service/classifier infrastructure.
- Introduce an `adaptive` wrapper that:
  - receives the same parser inputs the CLI already receives
  - decides which strategy to execute
  - runs the fallback cascade `regex -> layout -> llm`
  - evaluates each result for sensibility
  - stops at the first accepted result
  - or fails with full attempt-path diagnostics

### Wrapper Decision Model

- Deterministic candidate execution order:
  1. `regex`
  2. `layout`
  3. `llm`
- For each attempted strategy execution, capture:
  - strategy name
  - execution status
  - failure category or acceptance reason
  - warnings emitted by the attempted strategy
- Apply deterministic validity checks before or alongside LLM review:
  - chunk page ranges must be valid relative to the source PDF
  - output titles/filenames after the numeric prefix must be unique
- When produced file count is below `3`, require LLM sensibility review over each output before accepting the result
- The `llm` fallback step is still a parser strategy invocation, but it is attempted only after earlier strategies fail or are rejected

### LLM Mind Review Policy

- The LLM mind in feature 003 is not a parser; it is a reviewer over produced outputs.
- It reviews structured evidence about the current attempted result:
  - source page count
  - produced chunk count
  - normalized output suffixes/titles
  - per-chunk page spans
  - warnings and selected strategy
- It decides:
  - accept current result
  - reject current result and continue fallback
  - rationale for the decision
- Review should be bounded and practical for local inference; it must not prompt on raw full-book text.

### Default CLI Behavior

- If `--strategy` is omitted, CLI uses the adaptive wrapper path.
- If `--strategy` is provided, existing direct strategy behavior remains unchanged.
- This preserves explicit expert control while making the adaptive path the ergonomic default.

### Optional Dependency Policy

- Existing optional dependencies remain strategy-local.
- The adaptive wrapper must treat dependency/runtime failures as attempt outcomes, not fatal process failure, unless no later fallback path remains.
- LLM mind review and `llm` fallback both rely on the existing local `llama.cpp` runtime setup.

## Delivery Phases

### Phase 0 Research

- Define the exact acceptance/rejection criteria for a parser result in the adaptive wrapper.
- Decide where sensibility review belongs:
  - wrapper-local review component
  - or reuse/adapt feature-002 LLM review helpers
- Decide how to normalize output names for uniqueness checks.
- Produce `research.md` with decisions, rationale, and rejected alternatives.

### Phase 1 Design

- Write `data-model.md` for:
  - `StrategyAttempt`
  - `AdaptiveDecision`
  - `OutputSensibilityReview`
- Define contracts in `contracts/` for:
  - wrapper input/output invariants
  - fallback attempt semantics
  - sensibility review rules
- Draft `quickstart.md` showing:
  - parser run with omitted `--strategy`
  - explicit `--strategy adaptive`
  - fallback path examples
  - local `llama-server` requirements for sensibility review
- Re-check constitution gates with completed design artifacts.

### Phase 2 Planning Handoff

- Generate `tasks.md` from this plan with execution ordered by:
  1. wrapper scaffolding and direct deterministic checks
  2. LLM mind review over produced outputs
  3. CLI/service default path wiring
  4. docs and verification

## Test-First Execution Order

1. Add failing unit tests for wrapper attempt ordering and stopping rules.
2. Implement wrapper orchestration over existing parser/service calls until tests pass.
3. Add failing unit tests for deterministic sensibility checks:
   - filename uniqueness after numeric prefix removal
   - page-span sanity
   - low file count gating
4. Implement deterministic sensibility checks until tests pass.
5. Add failing unit tests for LLM mind acceptance/rejection over produced output summaries.
6. Implement bounded LLM sensibility review until tests pass.
7. Add CLI/service integration tests for omitted `--strategy` defaulting to adaptive.
8. Re-run existing direct-strategy tests to prove no regressions.

## Risks and Mitigations

- The wrapper may become too coupled to classifier internals.  
  - Mitigation: orchestrate at parser/service result boundaries, not inside classifiers.
- LLM sensibility review may introduce latency or fragile judgments.  
  - Mitigation: keep review bounded, use deterministic pre-checks first, and require structured rationale.
- Default adaptive behavior could surprise users who expect explicit strategy selection.  
  - Mitigation: preserve explicit `--strategy` support and document the default clearly.
- The `regex -> layout -> llm` cascade may skip potentially useful strategies like `index` or `heuristic`.  
  - Mitigation: document the chosen scope and leave broader cascades for future planning if needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
