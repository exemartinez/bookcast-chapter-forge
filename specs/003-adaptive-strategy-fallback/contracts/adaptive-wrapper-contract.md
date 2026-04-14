# Adaptive Wrapper Contract

## Purpose

The adaptive wrapper orchestrates parser strategy execution and result acceptance. It does not replace the existing classifier contract.

## Input Contract

- same parser inputs as the current CLI/service flow
- optional explicit `--strategy`
- when `--strategy` is omitted, adaptive is used by default

## Execution Contract

- fallback order defaults to `regex -> layout -> llm`
- each attempted strategy execution produces one `StrategyAttempt`
- failed or rejected attempts do not abort the process unless no fallback path remains

## Acceptance Contract

A current attempted result may be accepted only if:

- chunk page ranges are valid relative to the source PDF
- normalized output names after numeric prefix removal are unique
- if produced file count is below the configured threshold, wrapper-level LLM sensibility review accepts the result

## Failure Contract

The wrapper fails when:

- all fallback attempts fail or are rejected
- and no accepted result remains

The failure should include accumulated attempt-path diagnostics.
