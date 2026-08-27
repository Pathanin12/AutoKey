"""OCR อ่านชื่อ vendor จากแถว highlight ใน grid Express — ใช้ตอน verify หลังค้นหา"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from services.image_service import ImageService
from services.lookup_match_service import name_similarity
from services.tesseract_runtime_service import configure_tesseract


@dataclass(frozen=True)
class LookupOcrSettings:
    grid_region: tuple[int, int, int, int]
    name_x: tuple[int, int]
    row_height: int = 22
    lang: str = "tha"
    tesseract_cmd: str = ""


def read_highlighted_vendor_name(
    image: ImageService,
    settings: LookupOcrSettings,
    *,
    expected: str = "",
) -> str:
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
    pad_y = 2
    name_crop = screenshot.crop(
        (name_x0, max(0, row_y0 - pad_y), name_x1, row_y1 + pad_y),
    )
    return _read_best_ocr_text(name_crop, settings, expected=expected)


def _read_best_ocr_text(
    name_crop: "Image.Image",
    settings: LookupOcrSettings,
    *,
    expected: str = "",
) -> str:
    candidates: list[str] = []
    seen: set[str] = set()

    for mode in ("auto", "highlight", "normal"):
        prepared = _prepare_ocr_image(name_crop, mode=mode)
        for lang in _ocr_lang_candidates(settings.lang):
            text = _ocr_text(prepared, settings, lang=lang)
            if not text or text in seen:
                continue
            seen.add(text)
            candidates.append(text)

    if not candidates:
        return ""

    if expected.strip():
        return max(candidates, key=lambda text: name_similarity(expected, text))

    return candidates[0]


def _ocr_lang_candidates(lang: str) -> tuple[str, ...]:
    primary = lang.strip() or "tha"
    options: list[str] = [primary]
    if primary != "tha":
        options.append("tha")
    if "eng" not in primary and primary != "tha+eng":
        options.append("tha+eng")
    return tuple(dict.fromkeys(options))


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


def _is_blue_highlight(rgb) -> bool:
    import numpy as np

    mean = rgb.astype(float).mean(axis=(0, 1))
    red, green, blue = mean
    return blue > red + 12 and blue > green + 8 and blue > 70


def _prepare_ocr_image(image: "Image.Image", *, mode: str = "auto") -> "Image.Image":
    import cv2
    import numpy as np
    from PIL import Image

    rgb = np.asarray(image.convert("RGB"))
    highlight = mode == "highlight" or (mode == "auto" and _is_blue_highlight(rgb))
    normal = mode == "normal" or (mode == "auto" and not highlight)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)

    if highlight:
        # แถว highlight = ตัวอักษรขาวบนพื้นน้ำเงิน — แปลงเป็นดำบนขาวก่อน OCR
        _, bright = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)
        prepared = 255 - bright
    elif normal:
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, prepared = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        prepared = gray

    return Image.fromarray(prepared)


def _ocr_text(image: "Image.Image", settings: LookupOcrSettings, *, lang: str) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""

    if not configure_tesseract(settings.tesseract_cmd):
        return ""

    config = "--psm 7 --oem 1 -c preserve_interword_spaces=1"
    try:
        text = pytesseract.image_to_string(image, lang=lang, config=config)
    except Exception:
        return ""

    return " ".join(text.split()).strip()
