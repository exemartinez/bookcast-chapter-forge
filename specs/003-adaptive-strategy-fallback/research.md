# Research: Adaptive Strategy Fallback

## Decision Summary

- Implement feature `003` as a wrapper over the existing parser flow, not as a new classifier.
- Make the wrapper the default path when `--strategy` is omitted.
- Use a narrow fallback order of `regex -> layout -> llm`.
- Apply deterministic sensibility checks first.
- Use a bounded local-model review only when the produced file count is below the configured threshold.

## Rationale

The problem being solved is orchestration failure, not chapter-boundary extraction logic inside one classifier. Existing classifiers already represent the parsing strategies. What is missing is a wrapper that decides which one to try, when to continue, and when to stop.

The requested fallback order is intentionally narrow. It skips `index`, `semantic`, and `heuristic` even though some PDFs may benefit from them. That is acceptable for this feature because the goal is not to build the best possible universal cascade, but to add one explicit adaptive default path with predictable behavior.

## Alternatives Considered

### Alternative 1: Implement `adaptive` as a classifier

Rejected because the requested behavior sits above classification. It decides which strategy execution to run and evaluates produced outputs, which is parser-level orchestration rather than chapter classification.

### Alternative 2: Stop only on deterministic checks, no LLM mind

Rejected because the user explicitly wants a local-model judgment step for suspicious low-file-count cases.

### Alternative 3: Include more fallback strategies in the default cascade

Rejected for this feature because broader cascades make the behavior harder to reason about and harder to validate quickly. A future feature can widen the cascade if needed.

## Sensibility Review Rules

Deterministic checks:

- each chunk page range must stay within the source PDF page count
- normalized output names after the numeric prefix must be unique

Local-model review:

- required when produced file count is below the configured threshold
- reviews only produced-output summaries, not raw full-book text
- decides whether the current result is sensible enough to stop fallback

## Runtime Notes

- The wrapper reuses the existing local `llama.cpp` `llama-server` integration.
- If local-model review is required and `llama-server` is unavailable, the current result is treated as a failed/rejected adaptive attempt.
