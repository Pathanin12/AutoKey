from __future__ import annotations

from models.highlight_ocr_settings import HighlightOcrSettings
from models.lookup_ocr_check import LookupOcrCheck
from services.highlight_ocr.highlight_ocr_service import get_selected_text
from services.lookup_match_service import name_similarity, tidy_vendor_name


def check_highlighted_vendor(expected: str) -> LookupOcrCheck:
    """OCR แถวที่ไฮไลต์อยู่ แล้วเทียบกับชื่อที่ค้น"""
    query = tidy_vendor_name(expected)
    result = get_selected_text(HighlightOcrSettings())
    actual = tidy_vendor_name(result.text)
    return LookupOcrCheck(
        expected=query,
        actual=actual,
        similarity=name_similarity(query, actual),
    )
