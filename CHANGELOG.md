# Changelog

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
