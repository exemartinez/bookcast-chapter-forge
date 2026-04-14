# Contract: Interactive Wrapper

## Wrapper Responsibilities

The interactive wrapper must:

- create `books/` if it does not exist
- discover supported book files from `books/`
- allow single-file interactive selection
- collect strategy, config path, output directory, and JSON mode
- show a final execution preview
- require explicit confirmation before running the parser

## Delegation Rule

- The wrapper must delegate to the existing parser service/backend.
- It must not reimplement parsing, classification, or output writing logic.

## Cancellation Rule

- Entering `q`, `quit`, `exit`, or `cancel` at a prompt cancels the interactive session.
- Declining the final confirmation also cancels the session.
- Cancellation must not trigger parser execution.
