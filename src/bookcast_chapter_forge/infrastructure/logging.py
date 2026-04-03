from __future__ import annotations

import json
import logging


class EventLogger:
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

    def progress(self, event: str, **fields: object) -> None:
        self._emit("PROGRESS", event, **fields)

    def _emit(self, level: str, event: str, **fields: object) -> None:
        payload = {"level": level, "event": event, **fields}
        self._logger.info(json.dumps(payload, ensure_ascii=True))
