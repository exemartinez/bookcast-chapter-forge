# Quickstart: Interactive CLI Wrapper

## Launch the wrapper

```bash
./bookcast_forge.sh
```

## First-run behavior

- If `books/` does not exist, the wrapper creates it automatically.
- The wrapper then lists supported files found in `books/`.

## Interactive flow

The wrapper prompts for:

- source file
- strategy
- config path
- output directory
- JSON output mode

Then it shows a final execution preview and asks for confirmation.

## Cancellation

At any prompt, enter `q` to cancel.

If you decline the final confirmation, the parser is not run.
