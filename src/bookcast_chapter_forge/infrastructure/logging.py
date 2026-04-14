from __future__ import annotations

import json
import logging

EVENT_LAYOUT_EVIDENCE = "layout_evidence"
EVENT_BOUNDARY_DECISION = "boundary_decision"
EVENT_LLM_REVIEW = "llm_review"
EVENT_CLASSIFICATION_WARNING = "classification_warning"
EVENT_ADAPTIVE_ATTEMPT = "adaptive_attempt"
EVENT_ADAPTIVE_REVIEW = "adaptive_review"
EVENT_ADAPTIVE_WINNER = "adaptive_winner"


class EventLogger:
    """Emits structured JSON log events for CLI-visible diagnostics."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("bookcast_chapter_forge")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def info(self, event: str, **fields: object) -> None:
        self._emit("INFO", event, **fields)

    def error(self, event: str, **fields: object) -> None:
        self._emit("ERROR", event, **fields)

    def warning(self, event: str, **fields: object) -> None:
        """Emit a warning-level event without changing the JSON log shape."""
        self._emit("WARNING", event, **fields)

    def progress(self, event: str, **fields: object) -> None:
        self._emit("PROGRESS", event, **fields)

    def _emit(self, level: str, event: str, **fields: object) -> None:
        """Serialize one structured event as a single JSON line."""
        payload = {"level": level, "event": event, **fields}
        self._logger.info(json.dumps(payload, ensure_ascii=True))
