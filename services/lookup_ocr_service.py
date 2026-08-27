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


_OCR_PSM_MODES = ("7", "13", "6")


def read_highlighted_vendor_name(
    image: ImageService,
    settings: LookupOcrSettings,
    *,
    expected: str = "",
) -> str:
    if sys.platform != "win32":
        return ""

    screenshot = image.screenshot()
    grid = screenshot.crop(settings.grid_region)
    row_index = _find_highlight_row_index(grid, settings.row_height)
    if row_index is None:
        return ""

    grid_x0, grid_y0, _grid_x1, _grid_y1 = settings.grid_region
    row_y0 = grid_y0 + row_index * settings.row_height
    row_y1 = row_y0 + settings.row_height
    name_x0, name_x1 = _resolve_name_column_x(settings)
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

    for prepared in _prepare_ocr_variants(name_crop):
        for lang in _ocr_lang_candidates(settings.lang):
            for psm in _OCR_PSM_MODES:
                text = _ocr_text(prepared, settings, lang=lang, psm=psm)
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
    return tuple(dict.fromkeys(options))


def _resolve_name_column_x(settings: LookupOcrSettings) -> tuple[int, int]:
    """คอลัมน์ ชื่อข้อมูล อยู่ซ้ายสุดของ grid — clamp ไม่ให้ crop เริ่มกลางชื่อหรือลากไปถึง รหัส"""
    grid_x0, _grid_y0, grid_x1, _grid_y1 = settings.grid_region
    grid_width = max(1, grid_x1 - grid_x0)
    cfg_x0, cfg_x1 = settings.name_x

    name_x0 = min(cfg_x0, grid_x0 + 10)
    name_x1 = min(cfg_x1, grid_x0 + int(grid_width * 0.58))
    name_x0 = max(name_x0, grid_x0 + 4)
    name_x1 = max(name_x1, name_x0 + 80)
    return name_x0, name_x1


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


def _prepare_ocr_variants(image: "Image.Image") -> list["Image.Image"]:
    import cv2
    import numpy as np
    from PIL import Image

    rgb = np.asarray(image.convert("RGB"))
    highlight = _is_blue_highlight(rgb)
    variants: list[np.ndarray] = []

    if highlight:
        variants.extend(_highlight_masks(rgb))
    else:
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(otsu)

    prepared: list[Image.Image] = []
    kernel = np.ones((2, 2), np.uint8)
    for base in variants:
        scaled = cv2.resize(base, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
        closed = cv2.morphologyEx(scaled, cv2.MORPH_CLOSE, kernel)
        for img in (scaled, closed):
            bordered = cv2.copyMakeBorder(img, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=255)
            prepared.append(Image.fromarray(bordered))

    return prepared


def _highlight_masks(rgb) -> list:
    import cv2
    import numpy as np

    masks: list[np.ndarray] = []
    channels = cv2.split(rgb)
    brightness = sum(channel.astype(np.int16) for channel in channels) / 3.0

    for threshold in (150, 160, 170, 180):
        text_mask = brightness >= threshold
        black_on_white = np.where(text_mask, 0, 255).astype(np.uint8)
        masks.append(black_on_white)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    _, bright = cv2.threshold(gray, 165, 255, cv2.THRESH_BINARY)
    masks.append(255 - bright)

    return masks


def _ocr_text(
    image: "Image.Image",
    settings: LookupOcrSettings,
    *,
    lang: str,
    psm: str,
) -> str:
    try:
        import pytesseract
    except ImportError:
        return ""

    if not configure_tesseract(settings.tesseract_cmd):
        return ""

    config = f"--psm {psm} --oem 1 -c preserve_interword_spaces=1"
    try:
        text = pytesseract.image_to_string(image, lang=lang, config=config)
    except Exception:
        return ""

    return " ".join(text.split()).strip()
