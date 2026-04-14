# Changelog

## 0.3.0 - 2026-04-13

Additive adaptive-wrapper release for `bookcast-chapter-forge`.

Included:

- `adaptive` wrapper as the default parser path when `--strategy` is omitted
- primary adaptive cascade of `regex -> layout -> llm`
- deterministic output sensibility checks for invalid page spans and duplicate normalized output suffixes
- bounded local `llama.cpp` review for suspicious low-file-count adaptive results
- structured adaptive attempt/winner diagnostics in CLI and service output
- secondary recovery pool over `index`, `heuristic`, and `semantic` when the primary adaptive path runs dry

Important limitations:

- adaptive still relies on the quality of the underlying strategies rather than replacing them
- duplicate normalized output suffixes remain a hard rejection signal in the current adaptive policy
- the secondary fallback pool is randomized, so the recovery order among `index`, `heuristic`, and `semantic` is not fixed
- `model` remains available directly but is not part of the adaptive recovery path
- chapter extraction remains heuristic and PDF-dependent even when adaptive succeeds

## 0.2.0 - 2026-04-08

Additive heuristic expansion for `bookcast-chapter-forge`.

Included:

- `layout` classifier using page-local typography evidence
- `semantic` classifier using `unstructured` title/header elements
- deterministic `heuristic` classifier that integrates layout, semantic, regex, and index-derived evidence
- `llm` classifier that reviews layout-derived cuts through a local `Ollama` runtime with `phi3.5`
- expanded config support, CLI/service registration, structured logging diagnostics, and new classifier tests

Important limitations:

- all advanced strategies remain PDF-dependent and best-effort
- `semantic` can fail to find usable boundaries if semantic title extraction is weak
- `heuristic` is deterministic but can still produce wrong boundaries on exotic PDFs
- `llm` is a bounded reviewer over `layout`, not a whole-document autonomous parser

## 0.1.0 - 2026-04-07

Initial public baseline for `bookcast-chapter-forge`.

Included:

- fixed-page PDF chunking
- generic regex-based English-book chapter detection
- generic index/contents-based English-book chunking
- CLI, config loading, rollback-safe output writing, and automated tests

Important limitation:

- chapter extraction remains heuristic and PDF-dependent
- successful behavior varies with the source PDF's text layer, TOC structure, hyperlinks, outlines, and heading layout
- `0.1.0` should be understood as a useful baseline, not a universal chapter-segmentation guarantee
