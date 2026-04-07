# Feature 001 Closure

Feature `001-pdf-chapter-classifier` is closed as release `v0.1.0`.

## What Landed

- fixed-page PDF chunking
- regex-based generic English-book chapter detection
- index/contents-based best-effort chunking with offset inference
- CLI orchestration, YAML config loading, atomic PDF output writing, and automated tests

## What We Learned

- PDF chapter extraction is highly dependent on document makeup
- deterministic rules work well only when the PDF exposes enough structure
- TOC text, page labels, hyperlinks, outlines, and visible headings frequently disagree
- a generic parser can be useful, but it cannot honestly promise universal chapter segmentation

## Closed-State Assessment

`v0.1.0` is good enough to keep as a public baseline because:

- it demonstrates a real end-to-end chunking pipeline
- it has tests and documentation
- it works on some non-trivial real PDFs

`v0.1.0` is not the final answer because:

- some PDFs still segment incorrectly
- front matter and supplementary matter remain inconsistent
- the current `index` strategy is still heuristic, not authoritative

## Reason For Feature 002

Feature `002` exists to explore more explicitly heuristic and layout-aware strategies rather than stretching the current deterministic `001` implementation beyond what the PDFs themselves reliably support.
