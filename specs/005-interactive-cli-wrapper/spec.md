# Feature Specification: Interactive CLI Wrapper

**Feature Branch**: `005-interactive-cli-wrapper`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Create a proper CLI interface: run a simple script such as `bookcast_forge.sh` without parser parameters, start an interactive CLI, allow the user to pick files from the default `books/` folder, choose parser parameters interactively, and then invoke the existing parser pipeline."

## Scope

Feature `005` is additive. It introduces an interactive launcher over the existing parser CLI and service flow.

- The feature MUST provide a simple entrypoint such as `bookcast_forge.sh` and/or a Python interactive CLI command.
- The interactive wrapper MUST gather parser inputs from the user instead of requiring all parser flags up front.
- The wrapper MUST reuse the existing parser service and strategies rather than reimplementing parsing behavior.
- The default source directory for file selection MUST be `books/`.
- The wrapper MUST allow the user to choose parser parameters interactively and confirm the final execution plan before processing begins.
- The existing non-interactive parser CLI MUST remain available and behaviorally unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Launch And Run The Parser Interactively (Priority: P1)

As a developer or operator, I can run a simple wrapper command with no parser flags and complete a book-processing run by answering interactive prompts.

**Why this priority**: This is the core value of the feature. Without an interactive wrapper, the feature does not exist.

**Independent Test**: Can be tested independently by launching the wrapper with no parser flags, selecting one source file and one strategy, confirming the plan, and observing a successful parser execution.

**Acceptance Scenarios**:

1. **Given** the repository has supported source files in `books/`, **When** I run the interactive wrapper with no parser parameters, **Then** it prompts me to select a source file, choose execution options, confirm them, and launches the existing parser flow.
2. **Given** I complete the interactive prompts and confirm execution, **When** the wrapper invokes processing, **Then** the existing parser CLI/service runs with the selected values and writes outputs normally.
3. **Given** I cancel before confirmation, **When** the interactive session ends, **Then** no parser execution occurs.

---

### User Story 2 - Select Inputs And Parameters Safely (Priority: P2)

As an operator, I can see a clear list of candidate files from `books/`, choose one file, set the main parser parameters interactively, and avoid malformed command invocations.

**Why this priority**: The wrapper must reduce operational friction and input mistakes. That value depends on safe guided selection, not just launching a subprocess.

**Independent Test**: Can be tested independently by launching the wrapper, verifying file discovery from `books/`, selecting parameter values from prompts, and checking that the resulting parser invocation uses the chosen values.

**Acceptance Scenarios**:

1. **Given** supported source files exist in `books/`, **When** the wrapper starts, **Then** it lists those files for selection instead of requiring the user to type the full path manually.
2. **Given** I am configuring a run, **When** the wrapper prompts for parser options, **Then** I can choose values for at least strategy, config path, output directory, and JSON output mode.
3. **Given** the selected file or chosen options are invalid, **When** validation occurs before execution, **Then** the wrapper surfaces the issue clearly and lets me correct it or abort.

---

### User Story 3 - Preserve The Existing Non-Interactive Parser Path (Priority: P3)

As a developer, I can still use the existing non-interactive parser CLI directly, while the new interactive wrapper remains only an additive convenience layer.

**Why this priority**: The project already has a usable automation-friendly CLI. This feature must not break scripts, tests, or direct parser usage.

**Independent Test**: Can be tested independently by verifying that the interactive wrapper calls into the existing parser flow and that the current parser CLI still behaves the same when invoked directly.

**Acceptance Scenarios**:

1. **Given** the new interactive wrapper exists, **When** I run the existing parser CLI directly with explicit flags, **Then** it behaves the same as before this feature.
2. **Given** the interactive wrapper prepares a confirmed execution plan, **When** it launches processing, **Then** it delegates to the existing parser CLI/service rather than duplicating parser logic.
3. **Given** future parser strategies or options are added, **When** the wrapper is updated, **Then** it can expose them through prompt choices without changing the underlying parser contract.

### Edge Cases

- The `books/` directory does not exist.
- The `books/` directory exists but contains no supported files.
- The file list is large enough that selection must remain readable and deterministic.
- A selected file contains spaces, commas, apostrophes, or Unicode characters in its path.
- The chosen output directory already exists and contains previous outputs.
- The selected strategy requires local runtime prerequisites, such as `llama-server`, that are not available.
- The user aborts the interactive session at any prompt.
- The wrapper is launched from a different current working directory than the repository root.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a simple interactive launcher entrypoint such as `bookcast_forge.sh` or an equivalent Python wrapper command.
- **FR-002**: The interactive launcher MUST be runnable without supplying parser parameters on the command line.
- **FR-003**: The interactive launcher MUST discover candidate input files from the default `books/` directory.
- **FR-004**: The interactive launcher MUST present supported source files from `books/` as a user-selectable list.
- **FR-005**: The interactive launcher MUST support selecting at least one input file per run.
- **FR-006**: The interactive launcher MUST allow the user to configure the parser strategy interactively.
- **FR-007**: The interactive launcher MUST allow the user to configure or accept defaults for the config path, output directory, and JSON output mode.
- **FR-008**: The interactive launcher MUST show a final execution summary and require explicit user confirmation before invoking the parser.
- **FR-009**: If the user declines the final confirmation, the launcher MUST exit without running the parser.
- **FR-010**: The interactive launcher MUST call into the existing parser CLI/service rather than duplicating classification or output-writing logic.
- **FR-011**: The existing non-interactive parser CLI MUST remain available and behaviorally unchanged.
- **FR-012**: The interactive launcher MUST fail clearly when the `books/` directory is missing or contains no supported files.
- **FR-013**: The interactive launcher MUST handle file paths with whitespace and punctuation correctly when invoking the parser.
- **FR-014**: The interactive launcher MUST validate selected options before execution and surface correctable errors before starting the parser.
- **FR-015**: The interactive launcher MUST preserve default behavior where `books/` is the default input directory unless the user chooses a different path through the interactive flow.
- **FR-016**: Feature `005` MUST remain additive and MUST NOT redesign the underlying parser service, strategy system, or output-writing behavior.

### Key Entities *(include if feature involves data)*

- **InteractiveRunRequest**: The collected user selections for one run, including selected input file, strategy, config path, output directory, JSON mode, and confirmation state.
- **SelectableBookEntry**: One supported source file discovered in `books/` and shown in the interactive file picker.
- **ExecutionPreview**: The final summary shown to the user before confirmation, representing the exact parser values that will be executed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can start a parser run from the interactive wrapper without manually supplying parser flags.
- **SC-002**: The interactive wrapper can successfully list supported files from `books/` and launch the existing parser on a selected file.
- **SC-003**: A user can complete a confirmed interactive run in one continuous prompt flow without needing to edit shell commands.
- **SC-004**: Canceling the wrapper before confirmation results in zero parser execution side effects.
- **SC-005**: Existing direct parser CLI tests continue to pass without regression after the wrapper is added.

## Assumptions

- The wrapper targets local terminal usage, not a GUI.
- The default file-picking workflow is single-file selection from `books/`.
- Supported file types shown in the picker follow the parser’s currently supported source formats.
- The existing parser CLI and service remain the execution backend for the wrapper.
- Advanced users may still prefer the direct non-interactive parser CLI; this feature is for usability, not replacement.
