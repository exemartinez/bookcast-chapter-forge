# Data Model: Adaptive Strategy Fallback

## StrategyAttempt

Represents one attempted parser strategy execution inside the adaptive wrapper.

Fields:

- `strategy`: attempted strategy name
- `status`: `failed`, `rejected`, or `accepted`
- `reason`: human-readable failure or acceptance rationale

## OutputSensibilityReview

Represents the wrapper-level judgment for one attempted result.

Fields:

- `accepted`: whether fallback should stop on the current result
- `rationale`: explanation for accept/reject decision
- `review_source`: `deterministic` or `llm_mind`

## AdaptiveDecision

Represents the final adaptive orchestration outcome.

Fields:

- `attempts`: ordered tuple of `StrategyAttempt`
- `selected_strategy`: winning strategy name
- `review`: final `OutputSensibilityReview`

## ParserConfig Extensions

Feature `003` adds:

- `adaptive_fallback_order`
- `adaptive_min_output_files`
- `adaptive_prompt_instructions`

These control fallback ordering and wrapper-level sensibility review behavior.
