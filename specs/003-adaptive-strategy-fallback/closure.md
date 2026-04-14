# Closure: Adaptive Strategy Fallback

## Status

Implemented.

## Verification

- Focused wrapper tests:
  - `./bookcast-ve/bin/pytest tests/unit/test_adaptive_parser_wrapper.py tests/integration/test_pdf_parser_cli.py tests/integration/test_pdf_parser_service.py -q`
- Full suite:
  - `./bookcast-ve/bin/pytest -q`

## Results

- Focused wrapper tests: `22 passed`
- Full suite: `59 passed, 4 deselected`

## Outcome

Feature `003` adds an adaptive wrapper over the existing parser flow. It becomes the default path when `--strategy` is omitted, executes the primary `regex -> layout -> llm` cascade, applies deterministic sensibility checks, and uses bounded local-model review for suspicious low-file-count outputs. If that primary path runs dry, the wrapper now tries a randomized secondary pool of `index`, `heuristic`, and `semantic` before failing.
