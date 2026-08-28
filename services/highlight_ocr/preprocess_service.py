from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from models.highlight_ocr_settings import HighlightOcrSettings


def preprocess_image(bgr: np.ndarray, settings: HighlightOcrSettings) -> list[tuple[str, Image.Image]]:
    if bgr.size == 0:
        return []

    variants: list[tuple[str, Image.Image]] = []
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    if settings.denoise_strength > 0:
        gray = cv2.fastNlMeansDenoising(gray, None, settings.denoise_strength, 7, 21)

    contrast = cv2.convertScaleAbs(gray, alpha=settings.contrast_alpha, beta=settings.contrast_beta)
    scale = max(1.0, settings.upscale_factor)
    upscaled = cv2.resize(contrast, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    variants.append(("raw_upscaled", _to_pil(upscaled)))

    if settings.use_adaptive_threshold:
        adaptive = cv2.adaptiveThreshold(
            upscaled,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            8,
        )
        variants.append(("adaptive", _to_pil(adaptive)))

    blurred = cv2.GaussianBlur(upscaled, (3, 3), 0)
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu", _to_pil(otsu)))

    inverted = 255 - otsu
    variants.append(("otsu_inverted", _to_pil(inverted)))

    if not settings.try_raw_and_threshold:
        return variants[:1]

    return variants


def _to_pil(gray_or_bgr: np.ndarray) -> Image.Image:
    if len(gray_or_bgr.shape) == 2:
        rgb = cv2.cvtColor(gray_or_bgr, cv2.COLOR_GRAY2RGB)
    else:
        rgb = cv2.cvtColor(gray_or_bgr, cv2.COLOR_BGR2RGB)
    bordered = cv2.copyMakeBorder(rgb, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    return Image.fromarray(bordered)
