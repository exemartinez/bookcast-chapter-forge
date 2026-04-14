# Research: Interactive CLI Wrapper

## Decisions

### 1. Add a small Python interactive entrypoint plus a shell launcher

Decision:
- Implement the interactive flow in Python and expose it through `bookcast_forge.sh`.

Why:
- Prompt logic is easier to test in Python than in shell.
- The shell script can stay thin and only handle repository-relative execution.

Rejected alternatives:
- Implement the full prompt flow in Bash.
  - Rejected because testing and path handling would be more brittle.

### 2. Use standard-library prompts first

Decision:
- Use plain `input()` and `print()` based prompt orchestration.

Why:
- The feature only needs a small number of deterministic prompts.
- Avoids adding a prompt-library dependency for the first version.

Rejected alternatives:
- Add a prompt library such as `questionary` or `InquirerPy`.
  - Rejected because the current flow is simple enough without extra dependencies.

### 3. Delegate to the existing parser backend

Decision:
- The wrapper collects selections and then calls the existing parser service through the current CLI backend integration.

Why:
- This keeps the wrapper additive.
- It avoids duplicating parser execution logic.

### 4. Auto-create `books/` if it is missing

Decision:
- Treat missing `books/` as a bootstrap case and create it automatically.

Why:
- The wrapper is meant to lower startup friction.
- A missing `books/` directory is not an exceptional parser error; it is an onboarding condition.
