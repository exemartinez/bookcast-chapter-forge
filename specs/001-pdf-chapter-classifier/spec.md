# Feature Specification: PDF Chapter Classifier

**Feature Branch**: `001-pdf-chapter-classifier`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fixed-Page PDF chunking for NotebookLM upload limits (Priority: P1)

As a user, I want a Python CLI script that receives a PDF and produces N smaller PDF files when I choose a fixed-page strategy, so I can split oversized documents into NotebookLM-friendly chunks even before chapter detection is available.

The script must:

- accept a direct PDF input path
- read chunking parameters from `configs/config.yaml`
- create one output PDF per chunk in `output/`
- name outputs as `{input-file-name}-{order-number}.pdf`

**Why this priority**: It gives an immediate usable MVP even when chapter detection is not yet reliable.

**Independent Test**: Run the CLI against a synthetic 2-page PDF with `fixed_page.max_pages_per_chunk: 1` and confirm that 2 one-page PDFs are produced.

**Acceptance Scenarios**:

1. **Given** a 2-page PDF, **When** running the parser with `fixed` strategy and a maximum chunk size of 1, **Then** 2 output PDFs are created in `output/`

---

### User Story 2 - Generic regex-based chapter detection for English books (Priority: P2)

As a user, I want the parser to identify chapter boundaries for general English-language books without relying on domain-specific hardcoded title catalogs, so the software works across fiction, non-fiction, and other ordinary books.

The regex-based classifier must:

- operate on arbitrary English books, not only scripture-like PDFs
- use configurable patterns from `configs/config.yaml`
- detect likely chapter starts from generic structural signals such as:
  - headings like `Chapter 1`, `Part II`, `Section 3`
  - title pages for chapters without numeric prefixes
  - repeated heading forms inferred from the document itself
  - front-matter to body-matter transitions
- validate that the input looks like an English book before producing output
- avoid hardcoded domain-specific title catalogs in the default strategy

**Why this priority**: This is the first real chapter-identification capability and must be generic enough for public portfolio-quality software.

**Independent Test**: Run the regex strategy on at least one non-Bible English book with clear chapter headings and verify that output chunks align with real chapter starts.

**Acceptance Scenarios**:

1. **Given** an English-language non-fiction or fiction PDF with chapter headings, **When** running the parser with `regex` strategy, **Then** the output PDFs start at the detected chapter boundaries
2. **Given** a PDF whose structure does not look like an English book, **When** running the parser with `regex` strategy, **Then** the parser aborts with a clear validation error
3. **Given** a chaptered PDF, **When** running the parser with `regex` strategy, **Then** the implementation does not depend on a hardcoded title list for a specific corpus such as the books of the Bible

---

### User Story 3 - Generic index/contents-based chapter detection for English books (Priority: P3)

As a user, I want the parser to detect chapter boundaries from a generic table of contents or index page, so books with a usable contents page can be chunked more accurately than with regex-only detection.

The index-based classifier must:

- look for `Contents`, `Table of Contents`, or equivalent generic English contents-page signals
- parse chapter titles and printed page numbers from common contents layouts
- infer the offset between printed page numbers and PDF page indices
- map contents entries back to actual PDF pages
- use the strategy pattern so `fixed`, `regex`, and `index` remain selectable modes
- name outputs as `{input-file-name}-{order-number}-{chapter-name}.pdf`, with safe filename normalization and chapter-name truncation
- remain generic and must not depend on a domain-specific catalog such as Bible book names

**Why this priority**: Contents-driven parsing is a stronger generic strategy and should improve chapter accuracy for books with well-formed tables of contents.

**Independent Test**: Run the index strategy on at least one English book with a usable table of contents and verify that output chunks align with TOC-derived chapter starts.

**Acceptance Scenarios**:

1. **Given** an English PDF with a table of contents, **When** running the parser with `index` strategy, **Then** chunk boundaries are derived from parsed contents entries and PDF page offset inference
2. **Given** a PDF without a detectable contents page, **When** running the parser with `index` strategy, **Then** the parser aborts with a clear error and produces no partial output
3. **Given** a book with chapter names that contain spaces or punctuation, **When** output files are created, **Then** filenames are sanitized and truncated safely

---

### Edge Cases

- What happens when there is no identifiable contents/index page?
  - The parser aborts and writes no final output files.
- What happens when chapter headings are inconsistent?
  - The parser should prefer clear structural signals and fail explicitly when confidence is too low.
- How does the system handle long-running processing?
  - It always shows progress and allows the user to abort with `Ctrl-C`.
- What happens on interruption or write failure?
  - Final output must be rolled back so the run is effectively idempotent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST show progress throughout processing.
- **FR-002**: System MUST validate that the input is a PDF before processing.
- **FR-003**: Users MUST be able to abort processing with `Ctrl-C`, and the parser MUST roll back final output files.
- **FR-004**: System MUST provide a generic English-book regex strategy that does not depend on hardcoded title catalogs for a single domain or corpus.
- **FR-005**: System MUST allow chapter-detection heuristics to be configured from `configs/config.yaml`.
- **FR-006**: System MUST support batch processing of all `.pdf` files found in `books/`.
- **FR-007**: System MUST support a generic contents/index strategy for English books with detectable TOC-style pages.
- **FR-008**: System MUST fail with a clear validation error when it cannot confidently classify a document as a chaptered English book for the selected strategy.

### Key Entities *(include if feature involves data)*

- **Book**: the source PDF currently being analyzed
- **ChapterChunk**: a contiguous output slice with start page, end page, order, and optional chapter name
- **ParserConfig**: YAML-driven settings controlling validation and chunking heuristics
- **ClassificationResult**: the ordered result of one chunking strategy, including boundaries and metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The sum of output PDF page counts MUST equal the page count of the source PDF for successful runs.
- **SC-002**: The default regex strategy MUST not require a hardcoded domain-specific chapter-title catalog.
- **SC-003**: The parser MUST produce no final output files after interruption or fatal classification failure.
- **SC-004**: At least one general English book with ordinary chapter headings and at least one English book with a usable table of contents MUST be processed successfully by the corresponding strategies.

## Assumptions

- The application runs as a CLI in a Unix-like shell.
- Initial generic chapter detection scope is English-language books only.
- Domain-specific profiles may be added later, but they are out of scope for the default generic classifier.
