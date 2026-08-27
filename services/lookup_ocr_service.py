"""OCR อ่านชื่อ vendor จากแถว highlight ใน grid Express — ใช้ตอน verify หลังค้นหา"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from services.image_service import ImageService
from services.tesseract_runtime_service import configure_tesseract


@dataclass(frozen=True)
class LookupOcrSettings:
    grid_region: tuple[int, int, int, int]
    name_x: tuple[int, int]
    row_height: int = 22
    lang: str = "tha+eng"
    tesseract_cmd: str = ""


def read_highlighted_vendor_name(image: ImageService, settings: LookupOcrSettings) -> str:
    if sys.platform != "win32":
        return ""

    from PIL import Image

    screenshot = image.screenshot()
    grid = screenshot.crop(settings.grid_region)
    row_index = _find_highlight_row_index(grid, settings.row_height)
    if row_index is None:
        return ""

    grid_x0, grid_y0, _grid_x1, _grid_y1 = settings.grid_region
    row_y0 = grid_y0 + row_index * settings.row_height
    row_y1 = row_y0 + settings.row_height
    name_x0, name_x1 = settings.name_x
    name_crop = screenshot.crop((name_x0, row_y0, name_x1, row_y1))
    return _ocr_text(_prepare_ocr_image(name_crop), settings)


def _find_highlight_row_index(grid: "Image.Image", row_height: int) -> int | None:
    import numpy as np

    rgb = np.asarray(grid.convert("RGB"))
    height = rgb.shape[0]
    if height < row_height:
        return None

    row_count = max(1, height // row_height)
    best_index = 0
    best_score = float("-inf")

    for index in range(row_count):
        y0 = index * row_height
        y1 = min(y0 + row_height, height)
        band = rgb[y0:y1, :, :].astype(float)
        mean = band.mean(axis=(0, 1))
        luminance = 0.299 * mean[0] + 0.587 * mean[1] + 0.114 * mean[2]
        blue_excess = mean[2] - mean[0]
        white_distance = float(np.linalg.norm(mean - 255.0))
        score = white_distance + max(0.0, blue_excess) * 3.0 - luminance * 0.05
        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def _prepare_ocr_image(image: "Image.Image") -> "Image.Image":
    import cv2
    import numpy as np
    from PIL import Image

    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def _ocr_text(image: "Image.Image", settings: LookupOcrSettings) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""

    if not configure_tesseract(settings.tesseract_cmd):
        return ""

    config = "--psm 7 -c preserve_interword_spaces=1"
    try:
        text = pytesseract.image_to_string(image, lang=settings.lang, config=config)
    except Exception:
        try:
            text = pytesseract.image_to_string(image, lang="eng", config=config)
        except Exception:
            return ""

    return " ".join(text.split()).strip()
