from __future__ import annotations

from models.highlight_bbox import HighlightBBox
from models.highlight_ocr_settings import HighlightOcrSettings
from models.ocr_word_result import OcrLineResult, OcrWordResult


def filter_ocr_by_bbox(
    words: list[OcrWordResult],
    highlight_bbox: HighlightBBox,
    *,
    padding: int = 0,
) -> list[OcrWordResult]:
    filtered: list[OcrWordResult] = []
    for word in words:
        cx, cy = word.center
        if highlight_bbox.contains_point(cx, cy, padding=padding):
            filtered.append(word)
    return filtered


def words_to_line(
    words: list[OcrWordResult],
    highlight_bbox: HighlightBBox,
    *,
    engine: str,
) -> OcrLineResult:
    if not words:
        return OcrLineResult("", highlight_bbox, 0.0, tuple(), engine)

    words_sorted = sorted(words, key=lambda item: (item.bbox.x, item.bbox.y))
    text = " ".join(word.text for word in words_sorted if word.text.strip())
    confidence_values = [word.confidence for word in words_sorted if word.confidence > 0]
    confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0

    x0 = min(word.bbox.x for word in words_sorted)
    y0 = min(word.bbox.y for word in words_sorted)
    x1 = max(word.bbox.x1 for word in words_sorted)
    y1 = max(word.bbox.y1 for word in words_sorted)
    line_bbox = HighlightBBox(x0, y0, x1 - x0, y1 - y0, highlight_bbox.confidence)

    return OcrLineResult(text=text.strip(), bbox=line_bbox, confidence=confidence, words=tuple(words_sorted), engine=engine)


def merge_lines(lines: list[OcrLineResult]) -> str:
    return "\n".join(line.text for line in lines if line.text.strip())
