"""Highlight OCR services package."""

from services.highlight_ocr.highlight_ocr_service import get_selected_text
from services.highlight_ocr.highlight_detect_service import detect_highlight, get_highlight_bbox
from services.highlight_ocr.screen_capture_service import capture_screen
from services.highlight_ocr.crop_service import crop_highlight_region
from services.highlight_ocr.preprocess_service import preprocess_image
from services.highlight_ocr.ocr_engine_service import run_ocr
from services.highlight_ocr.filter_service import filter_ocr_by_bbox

__all__ = [
    "capture_screen",
    "detect_highlight",
    "get_highlight_bbox",
    "crop_highlight_region",
    "preprocess_image",
    "run_ocr",
    "filter_ocr_by_bbox",
    "get_selected_text",
]
