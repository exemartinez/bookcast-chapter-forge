# Data Model: Heuristic Chapter Detection

## Existing Types Reused

### `BookDocument`

- Parsed source PDF
- Holds `path`, `page_texts`, and optional title

### `ChapterChunk`

- Final chunk output
- Holds `order`, `start_page`, `end_page`, and optional title

### `ClassificationResult`

- Standard classifier contract output
- Holds chunks, warnings, and metadata

## Feature 002 Evidence Types

### `SignalEvidence`

- Source: one strategy-specific cue
- Fields:
  - `source`
  - `page`
  - `label`
  - `score`
- Used by `heuristic` to aggregate corroborating signals

### `BoundaryCandidate`

- Source: one proposed chapter start
- Fields:
  - `page`
  - `score`
  - `signals`
- Used by `heuristic` before final selection

### `BoundaryDecision`

- Source: final deterministic selection
- Fields:
  - `ordered_pages`
  - `rationale`
- Used to describe the chosen chapter plan

## Feature 002 LLM Review Types

### `LLMReviewPacket`

- Source: one `layout`-derived chunk candidate
- Fields:
  - `title`
  - `proposed_start_page`
  - `proposed_end_page`
  - `previous_title`
  - `next_title`
  - `context_excerpt`
- Purpose:
  - carry bounded local evidence into the Ollama prompt
  - avoid whole-document prompting

### `LLMReviewDecision`

- Source: one local-model response
- Fields:
  - `keep`
  - `corrected_title`
  - `rationale`
- Purpose:
  - decide whether to keep the proposed cut
  - correct the chunk title when the visible heading suggests a better label

## Config Additions

### `ParserConfig`

Added 002-specific fields:

- `layout_heading_patterns`
- `semantic_title_patterns`
- `heuristic_signal_weights`
- `llm_provider`
- `llm_model`
- `llm_base_url`
- `llm_timeout_seconds`
- `llm_review_window`
- `llm_max_excerpt_chars`
- `llm_prompt_instructions`
