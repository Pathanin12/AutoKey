from __future__ import annotations

from dataclasses import dataclass

from models.highlight_bbox import HighlightBBox
from models.ocr_word_result import OcrLineResult


@dataclass(frozen=True)
class HighlightOcrResult:
    text: str
    lines: tuple[OcrLineResult, ...]
    highlight_regions: tuple[HighlightBBox, ...]
    dpi_scale: float
    engine_used: str
    debug_dir: str | None = None

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def average_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(line.confidence for line in self.lines) / len(self.lines)
