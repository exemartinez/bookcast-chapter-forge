# Quickstart: Heuristic Chapter Detection

## Baseline deterministic run

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input books/example.pdf \
  --config configs/config.yaml \
  --strategy heuristic \
  --output-dir output/heuristic \
  --json
```

## Layout-only run

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input books/example.pdf \
  --config configs/config.yaml \
  --strategy layout \
  --output-dir output/layout \
  --json
```

## Semantic run

Requires `unstructured`.

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input books/example.pdf \
  --config configs/config.yaml \
  --strategy semantic \
  --output-dir output/semantic \
  --json
```

## Local LLM review run

Install and start `llama-server` first:

```bash
brew install llama.cpp
llama-server -hf ggml-org/gemma-3-1b-it-GGUF --port 8080
```

Then run:

```bash
PYTHONPATH=src python -m bookcast_chapter_forge.cli.pdf_parser \
  --input books/example.pdf \
  --config configs/config.yaml \
  --strategy llm \
  --output-dir output/llm \
  --json
```

## Expected failure modes

- Missing `pymupdf4llm`:
  - `layout` fails with a strategy-specific error
- Missing `unstructured`:
  - `semantic` fails with a strategy-specific error
- Missing or unreachable `llama-server` runtime:
  - `llm` fails with a strategy-specific error
