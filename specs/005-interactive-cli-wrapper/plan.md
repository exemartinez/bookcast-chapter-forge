# Implementation Plan: Interactive CLI Wrapper

**Branch**: `005-interactive-cli-wrapper` | **Date**: 2026-04-14 | **Spec**: `specs/005-interactive-cli-wrapper/spec.md`  
**Input**: Feature specification from `specs/005-interactive-cli-wrapper/spec.md`

## Summary

Add an interactive launcher over the existing parser CLI and service flow. The launcher should be invokable through a simple script such as `bookcast_forge.sh` with no parser flags, create `books/` if it does not exist, list supported source files from that directory, let the user choose parser options interactively, show a final execution preview, and then invoke the current parser pipeline without reimplementing parser behavior.

## Technical Context

**Language/Version**: Python 3.11 plus a small Bash wrapper  
**Primary Dependencies**: Existing parser stack (`argparse`, `pathlib`, parser services/classifiers); standard-library interactive input only unless design research justifies a lightweight prompt helper  
**Storage**: Local filesystem only (`books/`, `configs/`, `output/`)  
**Testing**: `pytest`  
**Target Platform**: macOS/Linux terminal environment  
**Project Type**: Single-package CLI application with one additive launcher script  
**Performance Goals**: Interactive prompt flow should feel immediate on local terminal startup; file discovery from `books/` should remain practical for ordinary local directories  
**Constraints**: Additive-only change, preserve existing parser CLI behavior, no parser redesign, safe handling of paths with spaces/punctuation, offline-capable  
**Scale/Scope**: Feature-local wrapper over one existing CLI/service path; single-file selection MVP from `books/`; no GUI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- OO-first modularity: Pass. The feature adds a wrapper layer and prompt orchestration rather than mixing interactive concerns into classifier logic.
- CLI-first interface: Pass. The feature is a terminal-first launcher and preserves the current CLI backend.
- Test-first workflow: Pass. Prompt selection, file discovery, cancellation, confirmation, and parser delegation can all be specified with failing tests first.
- Observability: Pass. Existing parser logging remains the execution backend; wrapper-level messaging can stay lightweight and local.
- Simplicity and additive evolution: Pass. The parser service remains the source of truth for execution; the wrapper only gathers inputs and delegates.
- Strategy isolation (VIII): Pass. This feature does not alter chapter-classification strategy behavior.
- Contract/data integrity (IX): Pass. The wrapper produces an execution request that maps directly to the existing parser CLI/service contract.
- Determinism (X): Pass. The prompt flow is user-driven, but file listing and execution preview should be deterministic for the same directory contents and choices.
- Dependency discipline (XI): Pass. The initial design assumes standard-library prompts unless research identifies a compelling need for a lightweight helper.
- Security/privacy (XII): Pass. Feature operates on local files and existing local parser execution only.

No constitution violations are required for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/005-interactive-cli-wrapper/
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
    │   ├── pdf_parser.py
    │   └── [interactive launcher module]
    ├── domain/
    │   └── entities.py
    ├── services/
    │   ├── pdf_parser_service.py
    │   └── [interactive runner/prompt orchestration helper if needed]
    └── infrastructure/
        └── [optional file-discovery/prompt utility if needed]

tests/
├── integration/
│   ├── test_pdf_parser_cli.py
│   └── [interactive launcher integration tests]
└── unit/
    └── [interactive wrapper unit tests]

bookcast_forge.sh
```

**Structure Decision**: Keep the existing single-package CLI architecture. Add one interactive launcher entrypoint and, if needed, a small supporting module under `src/bookcast_chapter_forge/cli/` or `services/`. Keep the parser service and current CLI as the backend execution path.

## Implementation Design

### Wrapper Execution Model

- Add a simple user-facing launcher command, expected to be `bookcast_forge.sh`.
- The shell script should invoke a Python interactive entrypoint within the project.
- The Python interactive entrypoint should:
  1. determine repository-relative defaults
  2. ensure `books/` exists, creating it if missing
  3. discover supported source files in `books/`
  4. prompt the user to choose one file
  5. prompt for strategy and core parser options
  6. show a final execution preview
  7. run the existing parser CLI/service only after explicit confirmation

### Interactive Input Scope

The initial interactive flow should gather:
- source file
- strategy
- config path
- output directory
- JSON output on/off

Optional parser flags beyond those can remain outside this first wrapper version unless research/design justifies exposing more.

### File Discovery Policy

- Default file-discovery directory is `books/`.
- If `books/` does not exist, create it automatically before file listing.
- Supported file types shown to the user must align with the parser’s currently supported formats.
- File listing should be deterministic and readable, even when filenames contain spaces or punctuation.

### Delegation Rule

- The interactive wrapper must not reimplement parsing logic.
- It must delegate to the current parser service or existing parser CLI entrypoint.
- The wrapper should construct a validated execution request and pass it through the existing backend path.

### Cancellation And Validation

- At any interactive step, the user must be able to abort without triggering parser execution.
- If file discovery yields no supported files, the wrapper should stop cleanly and explain what the user needs to add to `books/`.
- Before running the parser, the wrapper should validate the selected values and present a final preview.

## Delivery Phases

### Phase 0 Research

- Decide whether the interactive prompts should use only the Python standard library or a lightweight prompt library.
- Decide whether the wrapper should call the parser service directly or invoke the existing parser CLI entrypoint programmatically.
- Decide how repository-relative defaults such as `books/`, `configs/config.yaml`, and `output/` should be resolved when the wrapper is launched from different working directories.
- Produce `research.md` with decisions, rationale, and rejected alternatives.

### Phase 1 Design

- Write `data-model.md` for:
  - `InteractiveRunRequest`
  - `SelectableBookEntry`
  - `ExecutionPreview`
- Define prompt/validation contracts in `contracts/` for:
  - file discovery from `books/`
  - confirmation/cancel behavior
  - delegation to parser execution
- Draft `quickstart.md` showing:
  - launching `bookcast_forge.sh`
  - selecting a book from `books/`
  - confirming a run
  - cancellation behavior
  - automatic `books/` directory creation
- Re-check constitution gates with completed design artifacts.

### Phase 2 Planning Handoff

- Generate `tasks.md` from this plan with execution ordered by:
  1. wrapper data model and prompt flow tests
  2. file discovery and `books/` auto-create behavior
  3. execution preview and confirmation
  4. backend delegation through the existing parser path
  5. docs and verification

## Test-First Execution Order

1. Add failing unit tests for supported-file discovery and `books/` auto-creation.
2. Implement the file-discovery and wrapper request model until tests pass.
3. Add failing unit tests for interactive selection, cancellation, and execution preview behavior.
4. Implement the interactive wrapper flow until tests pass.
5. Add failing integration tests for launching the wrapper and delegating to the parser backend.
6. Implement the launcher script and backend delegation until tests pass.
7. Re-run existing parser CLI/service tests to prove no regression in the direct non-interactive path.

## Risks and Mitigations

- Interactive terminal behavior can be brittle to test directly.  
  - Mitigation: isolate prompt orchestration behind testable functions and keep terminal I/O thin.
- Repository-relative defaults may behave differently when launched from unexpected working directories.  
  - Mitigation: centralize path resolution and test it explicitly.
- The wrapper could drift from the parser CLI as new options are added.  
  - Mitigation: keep the wrapper intentionally narrow and delegate to the existing backend contract.
- Large `books/` directories could make selection noisy.  
  - Mitigation: keep the initial implementation deterministic and readable; defer search/filter enhancements unless needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
