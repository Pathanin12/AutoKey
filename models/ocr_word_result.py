from __future__ import annotations

from dataclasses import dataclass

from models.highlight_bbox import HighlightBBox


@dataclass(frozen=True)
class OcrWordResult:
    text: str
    bbox: HighlightBBox
    confidence: float
    engine: str

    @property
    def center(self) -> tuple[float, float]:
        return self.bbox.center


@dataclass(frozen=True)
class OcrLineResult:
    text: str
    bbox: HighlightBBox
    confidence: float
    words: tuple[OcrWordResult, ...]
    engine: str
