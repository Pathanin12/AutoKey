from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class HighlightOcrSettings:
    """ปรับ threshold ได้ทั้งหมด — ไม่ hard-code สี highlight เดียว"""

    # Highlight detection (LAB/HSV deviation จากพื้นหลัง)
    border_sample_px: int = 24
    min_color_distance: float = 12.0
    highlight_percentile: float = 97.5
    max_saturation_gray: int = 40
    min_value_delta: int = 18
    morph_kernel_w: int = 31
    morph_kernel_v: int = 3
    min_region_width: int = 80
    min_region_height: int = 10
    min_detection_confidence: float = 0.35

    # ขยาย bbox แนวตั้งให้ครอบทั้งบรรทัด
    line_expand_y_px: int = 6
    line_expand_x_px: int = 4

    # Preprocess
    upscale_factor: float = 3.0
    contrast_alpha: float = 1.6
    contrast_beta: int = 8
    denoise_strength: int = 7
    use_adaptive_threshold: bool = True
    try_raw_and_threshold: bool = True

    # OCR
    primary_engine: str = "auto"  # auto | tesseract | easyocr | paddleocr
    lang: str = "th"
    tesseract_cmd: str = ""
    tesseract_psm_modes: tuple[str, ...] = ("7", "6", "13")
    min_ocr_confidence: float = 0.25
    ocr_bbox_padding: int = 4

    # Debug
    debug: bool = False
    debug_dir: Path = field(default_factory=lambda: Path("debug/highlight_ocr"))

    # Screen (logical pixels — ตรงกับ pyautogui; scale จาก DPI อัตโนมัติ)
    target_logical_width: int | None = None
    target_logical_height: int | None = None
