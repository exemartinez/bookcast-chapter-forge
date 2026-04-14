# Quickstart: Adaptive Strategy Fallback

## Default Adaptive Run

When `--strategy` is omitted, the parser uses the adaptive wrapper by default.

```bash
PYTHONPATH=src ./bookcast-ve/bin/python -m bookcast_chapter_forge.cli.pdf_parser \
  --input "books/Building LLMs for Production_ Enhancing LLM Abilities -- Peters, Louie & Bouchard, Louis-François -- 2024.pdf" \
  --config configs/config.yaml \
  --output-dir output/adaptive-building-llms \
  --json
```

## Explicit Adaptive Run

```bash
PYTHONPATH=src ./bookcast-ve/bin/python -m bookcast_chapter_forge.cli.pdf_parser \
  --input "books/The-Holy-Bible-King-James-Version.pdf" \
  --config configs/config.yaml \
  --strategy adaptive \
  --output-dir output/adaptive-kjv \
  --json
```

## Direct Strategy Override

Explicit `--strategy` continues to bypass the adaptive wrapper.

```bash
PYTHONPATH=src ./bookcast-ve/bin/python -m bookcast_chapter_forge.cli.pdf_parser \
  --input "books/The-Holy-Bible-King-James-Version.pdf" \
  --config configs/config.yaml \
  --strategy layout \
  --output-dir output/layout-kjv \
  --json
```

## Local Model Requirement

Adaptive sensibility review reuses the local `llama.cpp` runtime.

```bash
llama-server -hf ggml-org/gemma-3-1b-it-GGUF --port 8080
```

This is only required when the adaptive wrapper reaches:

- the `llm` fallback step
- or low-file-count sensibility review
