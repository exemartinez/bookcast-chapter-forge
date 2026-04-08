# bookcast-chapter-forge

Turn long-form books into NotebookLM-ready PDF chunks for AI-generated podcast workflows.

Current baseline version: `0.1.0`

`bookcast-chapter-forge` is a Python CLI project that reads source PDFs, detects logical chunk boundaries, and exports one PDF per chunk. It currently supports:

- fixed-page chunking
- generic regex-based chapter/book-start detection for English books
- generic index/contents-driven chunking with page-offset inference for English books

## Feature Status

Feature `001-pdf-chapter-classifier` is closed as `v0.1.0`.

That version should be treated as a pragmatic baseline, not a universally reliable chapter parser. Results depend heavily on the PDF's internal structure:

- some PDFs work well because they expose usable TOCs, hyperlinks, outlines, or consistent heading typography
- some PDFs work only partially
- some PDFs will still fail to segment cleanly even when they are human-readable

The current implementation is intentionally documented as "best-effort generic PDF chunking" rather than "guaranteed chapter extraction."

## Current Scope

The first implemented feature focuses on PDF parsing and chunk generation.

- Input: local PDF files
- Output: one PDF per chunk in `output/`
- Strategies:
  - `fixed`
  - `regex`
  - `index`

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

## Usage

The source package lives under `src/`, so run the CLI with `PYTHONPATH=src`.

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

## Current Behavior

What `v0.1.0` does well:

- splits PDFs deterministically with `fixed`
- handles many ordinary English books with explicit `Chapter`, `Part`, or `Section` headings via `regex`
- handles some TOC-driven PDFs with `index`, especially when the PDF exposes:
  - printed TOC page numbers
  - clickable TOC destinations
  - outline/bookmark metadata
  - heading typography that can be detected locally near the predicted page

What `v0.1.0` does not guarantee:

- exact chapter segmentation for arbitrary PDFs
- correct front-matter handling across all books
- correct appendix/back-matter filtering across all books
- correct segmentation when the PDF text layer is noisy, missing, or inconsistent
- correct chapter detection when TOC text, page labels, hyperlinks, and visual headings disagree

## Testing

Run the full suite:

```bash
./bookcast-ve/bin/pytest
```

Current automated coverage includes:

- config loading
- fixed-page chunk generation
- regex and index classifier logic
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
- Bible-shaped PDFs expose the limits of a generic strategy very quickly:
  - Roman-numeral front matter may work in one file and fail in another
  - back matter may still be interpreted as a valid chunk
  - book boundaries may drift when TOC, page labels, and visible headings do not align cleanly
- Some books with rich internal structure are better described as "sections plus subsections" than pure chapters. The current implementation may over-segment or under-segment those documents.

## Next Steps

- define and evaluate `002` as a more explicitly heuristic chapter-analysis feature
- explore layout-aware extraction with tools such as `PyMuPDF` / `pymupdf4llm`
- explore semantic or model-assisted analysis when deterministic TOC parsing is not enough
- add EPUB ingestion
- improve package/install ergonomics so `PYTHONPATH=src` is no longer needed
- add NotebookLM export formatting beyond PDF chunking
