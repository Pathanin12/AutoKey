from __future__ import annotations

import numpy as np

from models.highlight_bbox import HighlightBBox
from models.highlight_ocr_settings import HighlightOcrSettings
from models.lookup_ocr_check import LookupOcrCheck
from models.ocr_word_result import OcrLineResult
from services.highlight_ocr.crop_service import crop_highlight_region
from services.highlight_ocr.filter_service import words_to_line
from services.highlight_ocr.highlight_detect_service import get_highlight_bbox
from services.highlight_ocr.ocr_engine_service import run_ocr
from services.highlight_ocr.preprocess_service import preprocess_image
from services.highlight_ocr.screen_capture_service import ScreenCapture, capture_screen
from services.lookup_match_service import name_similarity, tidy_vendor_name

_SCREEN = (1920, 1080)
_MAX_ROW_HEIGHT = 48
_MIN_ROW_HEIGHT = 12
_MIN_ROW_WIDTH = 100


def check_highlighted_vendor(
    expected: str,
    *,
    region: tuple[int, int, int, int] | None = None,
) -> LookupOcrCheck:
    """OCR เฉพาะแถวที่ไฮไลต์ในกริด lookup — ไม่อ่านทั้งหน้าจอ"""
    query = tidy_vendor_name(expected)
    settings = HighlightOcrSettings(
        primary_engine="tesseract",
        target_logical_width=_SCREEN[0],
        target_logical_height=_SCREEN[1],
        tesseract_psm_modes=("7", "6"),
        min_region_width=_MIN_ROW_WIDTH,
        min_region_height=_MIN_ROW_HEIGHT,
        line_expand_y_px=2,
        line_expand_x_px=6,
    )
    capture = capture_screen(
        target_logical_width=_SCREEN[0],
        target_logical_height=_SCREEN[1],
    )
    if region:
        capture = _crop_capture(capture, region)

    row = _first_row_bbox(capture.bgr, settings)
    actual = tidy_vendor_name(_ocr_bbox(capture.bgr, row, settings) if row else "")
    return LookupOcrCheck(
        expected=query,
        actual=actual,
        similarity=name_similarity(query, actual),
    )


def _crop_capture(capture: ScreenCapture, region: tuple[int, int, int, int]) -> ScreenCapture:
    x1, y1, x2, y2 = region
    x1 = max(0, min(x1, capture.image.width))
    y1 = max(0, min(y1, capture.image.height))
    x2 = max(x1 + 1, min(x2, capture.image.width))
    y2 = max(y1 + 1, min(y2, capture.image.height))
    image = capture.image.crop((x1, y1, x2, y2))
    bgr = np.ascontiguousarray(capture.bgr[y1:y2, x1:x2])
    return ScreenCapture(
        image=image,
        bgr=bgr,
        dpi_scale=capture.dpi_scale,
        logical_size=(image.width, image.height),
    )


def _first_row_bbox(bgr: np.ndarray, settings: HighlightOcrSettings) -> HighlightBBox | None:
    regions, _mask, _conf = get_highlight_bbox(bgr, settings)
    rows = [
        region
        for region in regions
        if _MIN_ROW_HEIGHT <= region.height <= _MAX_ROW_HEIGHT and region.width >= _MIN_ROW_WIDTH
    ]
    if not rows:
        return None
    rows.sort(key=lambda item: (item.y, item.x))
    return rows[0]


def _ocr_bbox(bgr: np.ndarray, region: HighlightBBox, settings: HighlightOcrSettings) -> str:
    cropped = crop_highlight_region(bgr, region)
    if cropped.size == 0:
        return ""
    best: OcrLineResult | None = None
    for _name, prepared in preprocess_image(cropped, settings):
        words = run_ocr(prepared, settings)
        line = words_to_line(words, region, engine="tesseract")
        if line.text and (best is None or line.confidence > best.confidence):
            best = line
    return best.text if best else ""
