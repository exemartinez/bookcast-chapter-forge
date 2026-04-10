# Feature Specification: Adaptive Strategy Fallback

**Feature Branch**: `003-adaptive-strategy-fallback`  
**Created**: 2026-04-10  
**Status**: Draft  
**Input**: User description: "Make adaptive the default strategy wrapper. It should receive all the usual parser parameters except an explicit strategy choice, decide what strategy is best, and follow a fallback cascade of regex -> layout -> llm. An LLM mind should evaluate whether produced output files are sensible and either accept them or continue the fallback path."

## Scope

Feature 003 is strictly additive. It introduces one new orchestration wrapper only.

- The system MUST keep the current architecture and pipeline shape.
- New logic MUST be implemented as a wrapper over the existing parser execution flow rooted in `src/bookcast_chapter_forge/cli/pdf_parser.py`.
- Existing `fixed`, `regex`, `index`, `layout`, `semantic`, `heuristic`, and `llm` strategies are out of scope for behavioral refactoring.
- The goal is fallback orchestration over existing strategies, not redesign of existing classifiers.
- The new orchestration strategy is the default user-facing path and SHOULD be exposed through a wrapper flow that does not require callers to choose a strategy explicitly.
- Any changes outside wrapper orchestration, default-selection glue, CLI/service integration, and minimal config glue are out of scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use Adaptive As Default Wrapper (Priority: P1)

As a developer, I can use the parser without providing an explicit strategy and have the system run the default `adaptive` wrapper, which decides what parser strategy to execute and follows a deterministic fallback cascade.

**Why this priority**: This is the core value of the feature. Without default adaptive orchestration, the feature does not exist.

**Independent Test**: Can be tested independently by invoking the parser through the default wrapper path on a PDF where an earlier strategy fails or produces unusable output and validating that the wrapper executes the next strategy in the cascade automatically.

**Acceptance Scenarios**:

1. **Given** a caller does not provide an explicit strategy, **When** the parser runs, **Then** it uses the `adaptive` wrapper by default instead of requiring direct classifier selection.
2. **Given** the default fallback cascade is configured as `regex -> layout -> llm`, **When** `regex` fails or produces unusable output, **Then** the `adaptive` strategy records that outcome and continues to `layout`.
3. **Given** the first attempted strategy produces output that is accepted as sensible, **When** the `adaptive` strategy runs, **Then** it does not invoke later fallback steps.

---

### User Story 2 - Use An LLM Mind To Judge Output Sensibility (Priority: P2)

As a developer, I can rely on an LLM mind to decide whether the current output files produced by one parser execution are sensible enough to stop or whether the adaptive wrapper should continue to the next fallback strategy.

**Why this priority**: The wrapper only becomes useful if it can reject suspicious results instead of stopping too early on bad output.

**Independent Test**: Can be tested independently by running the wrapper on outputs that violate one or more sensibility rules and verifying that the LLM mind rejects the result and advances the fallback cascade.

**Acceptance Scenarios**:

1. **Given** a strategy produces output files whose normalized names after the numeric prefix are not unique, **When** the LLM mind evaluates the result, **Then** it marks the output as not sensible and the adaptive cascade continues.
2. **Given** a strategy produces fewer than three output files, **When** the LLM mind evaluates the result, **Then** it inspects each produced file and decides whether the result is sensible or suspicious before allowing the cascade to stop.
3. **Given** a strategy produces output files where any produced chunk is obviously impossible relative to the source PDF, **When** the LLM mind evaluates the result, **Then** it rejects the result and the adaptive cascade continues.

---

### User Story 3 - Explain Adaptive Decisions (Priority: P3)

As a developer, I can inspect which parser executions were attempted, why a given result was rejected, and which final strategy won, so adaptive fallback remains debuggable.

**Why this priority**: Without structured diagnostics, fallback orchestration becomes hard to trust and hard to improve.

**Independent Test**: Can be tested independently by running the adaptive wrapper and verifying that metadata and warnings describe the attempted execution path, rejected outputs, and selected winner.

**Acceptance Scenarios**:

1. **Given** multiple attempted strategies, **When** the `adaptive` strategy finishes, **Then** result metadata includes the ordered attempt path and the selected winning strategy.
2. **Given** a strategy fails due to a dependency/runtime error, **When** the `adaptive` strategy continues, **Then** the failure reason is preserved in diagnostics instead of being silently swallowed.
3. **Given** no strategy succeeds, **When** the `adaptive` strategy ends, **Then** it fails clearly and reports the accumulated attempt-path diagnostics.

### Edge Cases

- `regex` fails outright while `layout` or `llm` remains usable.
- A strategy raises a runtime error versus returning zero chunks or clearly unusable chunks.
- A strategy returns chunks whose filenames collide after the numeric sequence prefix is ignored.
- A strategy returns only one or two files, which may indicate front matter, whole-book failure, or another suspicious outcome.
- A produced chunk exceeds the original PDF page count or violates chunk invariants such as overlap or out-of-range pages.
- The LLM mind is unavailable at runtime after `regex` or `layout` produces a candidate result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a new `adaptive` wrapper flow over the existing parser entrypoint in `src/bookcast_chapter_forge/cli/pdf_parser.py`.
- **FR-002**: The parser MUST support a default wrapper flow that uses `adaptive` when the caller does not explicitly choose a strategy.
- **FR-003**: The `adaptive` strategy MUST try existing strategies in this default deterministic order unless later planning explicitly changes it: `regex -> layout -> llm`.
- **FR-004**: Existing strategies (`fixed`, `regex`, `index`, `layout`, `semantic`, `heuristic`, `llm`) MUST remain independently selectable and behaviorally unchanged.
- **FR-005**: The `adaptive` wrapper MUST record each attempted strategy execution, its outcome, and the reason it failed, was rejected, or was accepted.
- **FR-006**: The wrapper MUST preserve compatibility with the existing parser output contract and CLI behavior.
- **FR-007**: The `adaptive` wrapper MUST fail clearly when no strategy execution produces acceptable output.
- **FR-008**: The `adaptive` wrapper MUST use an LLM mind to judge whether the current output files are sensible enough to stop or whether fallback should continue.
- **FR-009**: The LLM mind MUST verify that every produced output chunk is valid relative to the source PDF, including that each chunk page span is less than or equal to the source PDF page count.
- **FR-010**: The LLM mind MUST reject any result whose output filenames are not unique after removing the leading numeric sequence and separator.
- **FR-011**: When fewer than three output files are produced, the LLM mind MUST inspect each produced file and decide whether the result is sensible or suspicious before adaptive fallback may stop.
- **FR-012**: The `adaptive` wrapper MUST continue to the next fallback step when the current result is rejected by the LLM mind or by deterministic validity checks.
- **FR-013**: The `adaptive` wrapper MUST emit structured metadata and/or warnings describing the fallback path, rejected outputs, and selected winner.
- **FR-014**: Feature implementation MUST avoid classifier redesign and limit changes to the wrapper flow, default-selection glue, CLI/service integration, and minimal configuration/selection glue.
- **FR-015**: The `adaptive` wrapper MUST be deterministic for the same input document and configuration, except for the bounded local-model judgment step.

### Key Entities *(include if feature involves data)*

- **StrategyAttempt**: One attempted parser strategy execution, including strategy name, status, failure category or acceptance reason, and optional warning text.
- **AdaptiveDecision**: The final wrapper orchestration outcome, including ordered attempts, selected winner, and the LLM mind's acceptance or rejection reasoning.
- **OutputSensibilityReview**: The LLM mind's structured judgment over produced output files, including filename uniqueness, page-span sanity, low-file-count review, and stop-or-continue decision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new `adaptive` wrapper path is available through normal CLI/service usage and can be used as the default parser path.
- **SC-002**: On a PDF where `regex` fails and `layout` succeeds, `adaptive` continues automatically and returns the accepted later result without manual reruns.
- **SC-003**: On a PDF where an earlier fallback result is judged not sensible by the LLM mind, `adaptive` continues to the next fallback step instead of stopping early.
- **SC-004**: Existing non-adaptive strategy tests continue to pass without required behavior changes.
- **SC-005**: Adaptive-strategy tests cover dependency/runtime failures, rejected-output continuation, accepted-winner selection, and LLM sensibility checks for duplicate filenames and low file counts.
- **SC-006**: Every successful `adaptive` result includes structured diagnostics identifying attempted strategies, rejected outputs, and the selected winner.

## Assumptions

- Feature 003 targets English-language PDFs only; multilingual robustness is out of scope.
- Existing parser outputs and chunk invariants defined by features 001 and 002 remain the basis for deciding whether a result is acceptable.
- The default fallback order for feature 003 is `regex -> layout -> llm`.
- The LLM mind is a reviewer over produced outputs, not a replacement parser or classifier.
- This feature works over the same codebase and does not create a new application or separate pipeline.
