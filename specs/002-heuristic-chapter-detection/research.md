# Research: Heuristic Chapter Detection

## Decisions

### 1. Keep feature 002 additive

- Rejected a pipeline refactor.
- Chose new classifier strategies only.
- Reason: feature 001 is already the shipped baseline and must stay stable.

### 2. Use `pymupdf4llm` as the layout-oriented optional dependency

- Chosen for heading/layout-oriented evidence.
- Reason: it fits the need for page-local typography and structure cues without redesigning the reader pipeline.

### 3. Use `unstructured` as the semantic optional dependency

- Chosen for title/header element extraction.
- Reason: it provides a semantic signal source separate from plain regex matching.

### 4. Keep `heuristic` deterministic

- Chosen to integrate layout, semantic, regex, and index evidence with explicit weights and tie-breaks.
- Reason: deterministic output is easier to test, debug, and explain than jumping to a model too early.

### 5. Use `llama.cpp` `llama-server` for the LLM reviewer

- Chosen as the default local-model path for the `llm` strategy.
- Reason: it is lightweight, CLI-driven, GitHub-friendly, and exposes an OpenAI-compatible local server that matches the project's desired HOW-TO workflow.

### 6. Use the LLM as a reviewer, not as the parser

- The `llm` strategy starts from `layout` output.
- The model only reviews structured local evidence packets and returns:
  - keep or reject
  - corrected title
  - rationale
- Reason: this is cheaper, more explainable, and more robust than prompting over the whole document.

## Alternatives Considered

### LangGraph-first orchestration

- Rejected for MVP.
- Reason: extra orchestration complexity without proven value for the immediate problem.

### Whole-document LLM prompting

- Rejected.
- Reason: too expensive, too slow, and too difficult to constrain reliably for chapter-boundary decisions.

### Replacing existing strategies

- Rejected.
- Reason: feature 002 is explicitly additive and should not destabilize feature 001 behavior.
