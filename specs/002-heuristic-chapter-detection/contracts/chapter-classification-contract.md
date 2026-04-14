# Chapter Classification Contract

## Shared Contract

Every classifier strategy must:

- implement `ChapterClassifier`
- return `ClassificationResult`
- emit valid `ChapterChunk` ranges
- keep chunks ordered and non-overlapping
- fail with strategy-specific errors when optional dependencies are missing

## Strategy Expectations

### `layout`

- source of truth: page-local typography/layout evidence
- dependency: `pymupdf4llm`

### `semantic`

- source of truth: semantic title/header elements
- dependency: `unstructured`

### `heuristic`

- source of truth: deterministic aggregation of corroborating signals
- dependencies: only whichever subordinate strategies are selected and available

### `llm`

- source of truth: `layout` candidate cuts reviewed through structured local evidence
- dependency: reachable local `llama.cpp` `llama-server` runtime and configured lightweight GGUF model
- must not prompt over the full raw document
- must return keep/reject and corrected title decisions through standard `ClassificationResult`
