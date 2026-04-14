# bookcast-chapter-forge

Turn long-form books into NotebookLM-ready PDF chunks for AI-generated podcast workflows.

Current version: `0.3.0`

`bookcast-chapter-forge` is a Python CLI project that reads source PDFs, detects logical chunk boundaries, and exports one PDF per chunk. It currently supports:

- fixed-page chunking
- generic regex-based chapter/book-start detection for English books
- generic index/contents-driven chunking with page-offset inference for English books
- layout-aware heading detection
- semantic section detection
- deterministic heuristic signal integration
- local LLM review over layout-derived cuts
- adaptive wrapper fallback over parser strategies

## Feature Status

Feature `001-pdf-chapter-classifier` is closed as `v0.1.0`.
Feature `002-heuristic-chapter-detection` is implemented.
Feature `003-adaptive-strategy-fallback` adds the adaptive default wrapper flow.

That version should be treated as a pragmatic baseline, not a universally reliable chapter parser. Results depend heavily on the PDF's internal structure:

- some PDFs work well because they expose usable TOCs, hyperlinks, outlines, or consistent heading typography
- some PDFs work only partially
- some PDFs will still fail to segment cleanly even when they are human-readable

The current implementation is intentionally documented as "best-effort generic PDF chunking" rather than "guaranteed chapter extraction."

## Current Scope

The current implemented features focus on PDF parsing and chunk generation.

- Input: local PDF files
- Output: one PDF per chunk in `output/`
- Strategies:
  - `adaptive` (default wrapper)
  - `fixed`
  - `regex`
  - `index`
  - `layout`
  - `semantic`
  - `heuristic`
  - `llm`

## Project Structure

```text
src/bookcast_chapter_forge/
tests/
configs/config.yaml
books/
output/
specs/
```

## Setup

Create and use the local virtual environment:

```bash
python3 -m venv bookcast-ve
source bookcast-ve/bin/activate
pip install -r requirements.txt
```

Install optional strategy dependencies only if you plan to use them:

```bash
pip install pymupdf4llm
pip install unstructured
```

Install and run the local `llama.cpp` server if you plan to use `llm` directly or allow `adaptive` to reach LLM-backed review:

```bash
brew install llama.cpp
llama-server -hf ggml-org/gemma-3-1b-it-GGUF --port 8080
```

## Usage

The source package lives under `src/`, so run the CLI with `PYTHONPATH=src`.

Split a single PDF with the default adaptive wrapper:

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf" \
  --config configs/config.yaml \
  --output-dir output \
  --json
```

Split a single PDF with the fixed-page strategy:

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf" \
  --config configs/config.yaml \
  --strategy fixed \
  --output-dir output \
  --json
```

Run generic regex-based chunking:

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input books/CSB_Pew_Bible_2nd_Printing.pdf \
  --config configs/config.yaml \
  --strategy regex \
  --output-dir output
```

Run index-based chunking:

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input books/CSB_Pew_Bible_2nd_Printing.pdf \
  --config configs/config.yaml \
  --strategy index \
  --output-dir output
```

Run optional advanced strategies:

```bash
# Layout-aware strategy (requires optional dependency: pymupdf4llm)
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser --input books/example.pdf --config configs/config.yaml --strategy layout --output-dir output

# Semantic strategy (requires optional dependency: unstructured)
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser --input books/example.pdf --config configs/config.yaml --strategy semantic --output-dir output

# Model-assisted strategy (currently experimental and not part of adaptive recovery)
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser --input books/example.pdf --config configs/config.yaml --strategy model --output-dir output

# Hybrid heuristic integrator
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser --input books/example.pdf --config configs/config.yaml --strategy heuristic --output-dir output

# LLM review strategy (requires local llama.cpp llama-server)
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser --input books/example.pdf --config configs/config.yaml --strategy llm --output-dir output

# Adaptive wrapper (default if --strategy is omitted)
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser --input books/example.pdf --config configs/config.yaml --strategy adaptive --output-dir output
```

Process all PDFs in `books/`:

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --books-dir books \
  --config configs/config.yaml \
  --strategy fixed \
  --output-dir output
```

## Configuration

The chunking behavior is configured in `configs/config.yaml`.

- `fixed_page.max_pages_per_chunk`: hard page limit per chunk
- `regex.*`: generic English-book chapter heading heuristics
- `index.*`: generic English contents/index-page detection and entry parsing rules
- `layout.*`: layout-heading matching patterns
- `semantic.*`: semantic title-matching patterns
- `heuristic.*`: deterministic signal weights
- `llm.*`: local llama-server review settings for validating layout-derived cuts
- `adaptive.*`: fallback order and sensibility-review thresholds for the default wrapper flow

## Optional Dependencies

- `pymupdf4llm`: required for `layout`
- `unstructured`: required for `semantic`
- local `llama.cpp` `llama-server`: required for `llm`
- local `llama.cpp` `llama-server`: also required when `adaptive` reaches low-file-count LLM sensibility review or the `llm` fallback step

## Current Behavior

What `v0.3.0` does well:

- splits PDFs deterministically with `fixed`
- handles many ordinary English books with explicit `Chapter`, `Part`, or `Section` headings via `regex`
- handles some TOC-driven PDFs with `index`, especially when the PDF exposes:
  - printed TOC page numbers
  - clickable TOC destinations
  - outline/bookmark metadata
  - heading typography that can be detected locally near the predicted page
- detects some chapter starts from layout signals when typography is stronger than the text-only layer
- can use semantic title elements when `unstructured` produces usable title blocks
- can review layout-derived cuts with a bounded local LLM prompt when `llm` is selected
- can use `adaptive` as the default parser path and automatically try the primary cascade `regex -> layout -> llm`
- if that primary adaptive path runs dry, it can continue into a secondary recovery pool containing `index`, `heuristic`, and `semantic`

What `v0.3.0` does not guarantee:

- exact chapter segmentation for arbitrary PDFs
- correct front-matter handling across all books
- correct appendix/back-matter filtering across all books
- correct segmentation when the PDF text layer is noisy, missing, or inconsistent
- correct chapter detection when TOC text, page labels, hyperlinks, and visual headings disagree
- correct semantic section extraction on every PDF, even when `unstructured` is installed
- perfect local-LLM review; `llm` is limited to the structured packet derived from `layout`

## Testing

Run the full suite:

```bash
./bookcast-ve/bin/pytest
```

Current automated coverage includes:

- config loading
- fixed-page chunk generation
- regex and index classifier logic
- layout, semantic, heuristic, and llm classifier logic
- atomic PDF writing
- CLI and service integration paths

## Verified Scenarios

The current implementation was validated against:

- synthetic fixture PDFs in the automated test suite
- `books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf` with:
  - `regex` strategy: 13 output PDFs from generic chapter-heading detection
  - `index` strategy: 12 output PDFs from `Chapter I` through `Chapter XII`
- `books/CSB_Pew_Bible_2nd_Printing.pdf` with:
  - `regex` strategy: 66 output PDFs
  - `index` strategy: mixed results depending on front-matter and supplementary-material interpretation
- `books/The-Holy-Bible-King-James-Version.pdf` with:
  - `index` strategy: partly correct book-level chunking, but still known to mis-handle some later-book and trailing supplementary-material cases

## Known Limitations

- `index` is still heuristic. It is not a canonical chapter parser.
- PDFs with bad text extraction, weak TOCs, or conflicting metadata can still produce incorrect boundaries.
- `layout` can still misread visually prominent preface or table-of-contents pages as chapters.
- `semantic` may return no useful section boundaries when the semantic partitioner cannot recover good title elements.
- `model` remains experimental and is not trusted enough to be part of the adaptive recovery path.
- `heuristic` is deterministic and explainable, but exotic PDFs can still defeat combined signals.
- `llm` is a second-pass reviewer over `layout`, not a full autonomous parser or a whole-document reasoning system.
- `adaptive` is a wrapper over parser execution, not a replacement for explicit strategy control.
- `adaptive` keeps hard rejection of duplicate normalized output suffixes in the current policy, which can still reject some documents that were mechanically chunked.
- Bible-shaped PDFs expose the limits of a generic strategy very quickly:
  - Roman-numeral front matter may work in one file and fail in another
  - back matter may still be interpreted as a valid chunk
  - book boundaries may drift when TOC, page labels, and visible headings do not align cleanly
- Some books with rich internal structure are better described as "sections plus subsections" than pure chapters. The current implementation may over-segment or under-segment those documents.

## Next Steps

- strengthen real-book evaluation for `layout`, `heuristic`, and `llm`
- improve package/install ergonomics so `PYTHONPATH=src` is no longer needed
- add EPUB ingestion
- add NotebookLM export formatting beyond PDF chunking
