from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bookcast_chapter_forge.infrastructure.logging import EventLogger
from bookcast_chapter_forge.services.output_writer import OutputWriter
from bookcast_chapter_forge.services.pdf_parser_service import PdfParserService


def build_service(output_dir: str | Path = "output") -> PdfParserService:
    return PdfParserService(output_writer=OutputWriter(output_dir=output_dir), logger=EventLogger())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split PDF books into chapter-ready chunks")
    parser.add_argument("--input", help="Path to a single PDF file")
    parser.add_argument("--books-dir", default="books", help="Directory containing PDF books")
    parser.add_argument("--config", default="configs/config.yaml", help="Path to the YAML config file")
    parser.add_argument("--strategy", choices=["fixed", "regex", "index"], default="fixed")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    service = build_service(output_dir=args.output_dir)
    try:
        processed = service.process(
            strategy=args.strategy,
            config_path=args.config,
            input_path=args.input,
            books_dir=None if args.input else args.books_dir,
        )
    except KeyboardInterrupt:
        print("Processing aborted by user", file=sys.stderr)
        return 130
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "strategy": args.strategy,
            "processed_books": [
                {
                    "source": str(item.source),
                    "chunk_count": item.chunk_count,
                    "output_files": [str(path) for path in item.output_files],
                }
                for item in processed
            ],
        }
        print(json.dumps(payload))
    else:
        for item in processed:
            print(f"{item.source} -> {item.chunk_count} chunk(s)")
            for output in item.output_files:
                print(f"  - {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
