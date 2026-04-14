# Closure: Heuristic Chapter Detection

## Status

Feature `002-heuristic-chapter-detection` is implemented as an additive expansion over feature `001`.

## Delivered

- `layout` classifier
- `semantic` classifier
- deterministic `heuristic` classifier
- `llm` classifier using local `llama.cpp` `llama-server` review over `layout` candidates
- config, CLI, service registration, structured diagnostics, and automated tests

## Verification

- `./bookcast-ve/bin/pytest -q` -> `42 passed, 4 deselected`
- strategy-level unit tests cover:
  - layout dependency and heading evidence behavior
  - semantic dependency and title-element behavior
  - heuristic ordering and scoring behavior
- direct local runtime validation succeeded with:
  - `llama-server -hf ggml-org/gemma-3-1b-it-GGUF --port 8080`
  - OpenAI-compatible `POST /v1/chat/completions`
  - llm review packet construction and local runtime failure behavior

## Limits

- advanced strategies remain heuristic and PDF-dependent
- `llm` review is bounded by the evidence packet built from `layout`, not whole-document reasoning
