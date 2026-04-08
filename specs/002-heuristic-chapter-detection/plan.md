# Implementation Plan: Heuristic Chapter Detection

**Branch**: `002-heuristic-chapter-detection` | **Date**: 2026-04-08 | **Spec**: `specs/002-heuristic-chapter-detection/spec.md`  
**Input**: Feature specification from `specs/002-heuristic-chapter-detection/spec.md`

## Summary

Add new chapter-detection strategies as additive modules implementing the existing `ChapterClassifier` contract, without refactoring current `fixed`, `regex`, or `index` behavior. Delivery order is: (1) layout-aware classifier, (2) semantic section classifier, (3) hybrid heuristic integrator that combines multiple corroborating deterministic signals into final boundary decisions, and (4) a local-LLM enhancer that starts from `layout` candidates and uses `Ollama + phi3.5 mini` to validate cuts and correct titles. The existing CLI/service pipeline remains intact; only strategy registration and classifier-local glue are touched.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Existing: `pypdf`, `PyYAML`, `pytest`; Optional for this feature: `pymupdf4llm`, `unstructured`, `langchain-ollama` or a thin Ollama HTTP adapter, local `Ollama` runtime with `phi3.5` mini  
**Storage**: Local filesystem only (`books/`, `configs/`, `output/`)  
**Testing**: `pytest`, `pytest-cov` (unit + integration; slow markers for larger real-book scenarios)  
**Target Platform**: macOS/Linux CLI environment  
**Project Type**: Single-package CLI application  
**Performance Goals**: Maintain practical local processing performance for book-sized PDFs while preserving deterministic non-model modes  
**Constraints**: Additive-only strategy implementation, strict `ChapterClassifier` contract compatibility, optional dependencies must fail in isolation, offline-first defaults, structured logging, deterministic tie-breaks for heuristic decisions, LLM review restricted to structured local evidence derived from `layout` outputs  
**Scale/Scope**: Feature-local classifier additions for English-language PDFs; no architecture rewrite; no global dependency hard requirement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- OO-first modularity: Pass. New behavior is introduced via new classifier classes.
- CLI-first interface: Pass. Existing CLI surface remains the entry point.
- Test-first workflow: Pass. Each classifier and integration path is test-defined before implementation.
- Observability: Pass. New strategies emit structured strategy-level progress/warning events.
- Simplicity and additive evolution: Pass. No redesign of orchestration; registration + isolated strategy modules only.
- Strategy isolation (VIII): Pass by design requirement.
- Contract/data integrity (IX): Pass with explicit chunk validity rules.
- Determinism (X): Pass for non-LLM modes; LLM-enhanced review remains optional/experimental.
- Dependency discipline (XI): Pass with optional import guards and isolated failures.
- Security/privacy (XII): Pass with structured evidence to local model and no mandatory external network calls.

No constitution violations are required for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/002-heuristic-chapter-detection/
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
    │   ├── index_chapter_classifier.py
    │   ├── layout_aware_classifier.py          # new
    │   ├── semantic_section_classifier.py      # new
    │   ├── heuristic_integrator_classifier.py  # new final deterministic integrator
    │   └── llm_enhanced_classifier.py          # new layout + Ollama reviewer
    └── infrastructure/
        ├── logging.py
        └── pdf_reader.py

configs/
└── config.yaml

tests/
├── unit/
└── integration/
```

**Structure Decision**: Keep the existing single-package architecture. Add strategy-specific modules under `classifiers/` and minimal registration/config updates only. No service/pipeline redesign.

## Implementation Design

### Core Objects and Evidence Model

- Reuse existing `ChapterClassifier`, `BookDocument`, `ClassificationResult`, and `ChapterChunk` contracts.
- Introduce internal evidence abstractions (implemented as dataclasses in classifier modules or domain extensions):
  - `SignalEvidence`: source signal + confidence inputs
  - `BoundaryCandidate`: candidate start location + supporting evidence
  - `BoundaryDecision`: resolved ordered boundaries used to build `ChapterChunk`s
  - `LLMReviewPacket`: structured local evidence bundle for one proposed `layout` cut
  - `LLMReviewDecision`: keep/reject/title-correction response from the local model
- Keep output contract unchanged: all strategies return `ClassificationResult`.

### Strategy Delivery Order

1. **Layout-aware classifier (P1)**  
   Uses `pymupdf4llm` when available to infer starts from heading hierarchy, typography, spacing, and block segmentation.

2. **Semantic section classifier (P2)**  
   Uses `unstructured` title/section segmentation as an additional deterministic signal source.

3. **Hybrid heuristic integrator (P3, last)**  
   Aggregates evidence from layout-aware + semantic signals plus TOC/page-label/hyperlink/outline cues into final deterministic boundary decisions.

4. **LLM enhancer (P4, after deterministic strategies)**  
   Starts from `layout`-proposed chunks, builds structured local review packets, and uses `Ollama + phi3.5 mini` to confirm/reject each cut and correct chunk titles/filenames.

### Registration and Selection

- Add new selectable strategy names in CLI/service classifier map.
- Strategy names should remain explicit and independently selectable (e.g., `layout`, `semantic`, `heuristic`, `llm`).
- Existing `fixed|regex|index` behavior remains unchanged.

### Optional Dependency Policy

- Optional imports are lazy and classifier-local.
- Missing optional packages produce clear strategy-specific errors.
- Baseline install (without optional packages) continues to run existing strategies.
- The LLM-enhanced strategy additionally requires a reachable local `Ollama` runtime and the configured `phi3.5` mini model to be available.

### Deterministic Decision Policy

- Heuristic and non-model paths must be deterministic for same input/config.
- Tie-break rules are explicit and documented (signal precedence and confidence ordering).
- LLM-enhanced review consumes structured local evidence packets only; raw full-document prompts are out of scope.
- The LLM review layer is advisory over `layout` output and must return structured keep/reject/title decisions.

## Delivery Phases

### Phase 0 Research

- Research robust layout-signal extraction patterns using `pymupdf4llm`.
- Research `unstructured` element taxonomy for chapter/section detection.
- Define candidate-scoring and deterministic tie-break policy for integrator.
- Define LLM review packet schema, prompt contract, and local `Ollama + phi3.5 mini` runtime constraints.
- Produce `research.md` with decisions, rationale, and alternatives.

### Phase 1 Design

- Write `data-model.md` for evidence and decision objects.
- Define contracts in `contracts/` for strategy selection, classifier output invariants, and strategy-specific failure semantics.
- Draft `quickstart.md` showing:
  - baseline run without optional deps
  - strategy-specific runs with optional deps
  - expected behavior on dependency-missing paths
  - local `Ollama` setup and `phi3.5` mini pull instructions for the LLM enhancer
- Re-check constitution gates with completed design artifacts.

### Phase 2 Planning Handoff

- Generate `tasks.md` from this plan with implementation ordered by P1 -> P2 -> P3 -> P4.
- Ensure task graph keeps the LLM enhancer after `layout` and after the deterministic strategies are stable.

## Test-First Execution Order

1. Add failing unit tests for layout-aware classifier contract validity and dependency-missing behavior.
2. Implement layout-aware classifier until tests pass.
3. Add failing unit tests for semantic classifier contract/dependency behavior.
4. Implement semantic classifier until tests pass.
5. Add failing unit/integration tests for hybrid integrator combining deterministic signals from prior strategies.
6. Implement hybrid integrator and deterministic tie-break rules until tests pass.
7. Add failing unit/integration tests for the LLM enhancer reviewing `layout` cuts and correcting titles.
8. Implement local `Ollama + phi3.5 mini` review flow until tests pass.
9. Add CLI/service integration tests for registration and independent strategy selection.
10. Re-run existing `fixed|regex|index` tests to prove no regressions.

## Risks and Mitigations

- Optional dependency fragility across environments.  
  - Mitigation: lazy imports, clear error messages, isolated strategy failures.
- Signal disagreement causing unstable chapter boundaries.  
  - Mitigation: explicit scoring + deterministic tie-break hierarchy + warning metadata.
- LLM-enhanced review introducing nondeterminism, latency, or runtime friction.  
  - Mitigation: keep optional/experimental, bounded structured evidence input, local `Ollama` only, deterministic fallback/error path when runtime is unavailable.
- Overreaching scope into pipeline refactor.  
  - Mitigation: enforce additive-only tasks; reject non-essential orchestration changes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
