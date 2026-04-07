# bookcast-chapter-forge

Turn long-form books into NotebookLM-ready PDF chunks for AI-generated podcast workflows.

`bookcast-chapter-forge` is a Python CLI project that reads source PDFs, detects logical chunk boundaries, and exports one PDF per chunk. It currently supports:

- fixed-page chunking
- generic regex-based chapter/book-start detection for English books
- generic index/contents-driven chunking with page-offset inference for English books

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
- `books/CSB_Pew_Bible_2nd_Printing.pdf` with:
  - `regex` strategy: 66 output PDFs
  - `index` strategy: 68 output PDFs from generic contents parsing, including trailing supplementary contents entries

## Next Steps

- add EPUB ingestion
- improve package/install ergonomics so `PYTHONPATH=src` is no longer needed
- improve generic chapter heuristics for books with title-only chapter pages
- add NotebookLM export formatting beyond PDF chunking
