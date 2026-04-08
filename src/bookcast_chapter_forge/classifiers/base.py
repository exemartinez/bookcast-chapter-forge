from __future__ import annotations

from abc import ABC, abstractmethod

from bookcast_chapter_forge.domain.entities import BookDocument, ClassificationResult, ParserConfig


class ChapterClassifier(ABC):
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def classify(self, book: BookDocument, config: ParserConfig) -> ClassificationResult:
        raise NotImplementedError
