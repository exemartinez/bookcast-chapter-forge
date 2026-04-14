#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHONPATH=src "${PYTHON:-python}" -m bookcast_chapter_forge.cli.interactive_cli
