"""จับภาพ template ด้วย OpenCV matchTemplate — TM_CCORR_NORMED (+ mask ถ้ามี alpha)"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment,misc]

MATCH_METHOD = cv2.TM_CCORR_NORMED
MATCH_METHOD_OPAQUE = cv2.TM_CCOEFF_NORMED


@dataclass(frozen=True)
class TemplateMatchResult:
    found: bool
    score: float
    x: int
    y: int
    expected_x: int
    expected_y: int

    @property
    def offset(self) -> tuple[int, int]:
        return self.x - self.expected_x, self.y - self.expected_y


def load_image(path: Path) -> Image.Image:
    if Image is None:
        raise RuntimeError("ติดตั้ง Pillow ก่อน: pip install Pillow")
    return Image.open(path).convert("RGBA")


def load_step_template(step) -> Image.Image:
    image = load_image(step.template_path)
    crop_box = step.crop_box()
    if crop_box is None:
        return image
    return image.crop(crop_box)


def _pil_to_cv(image: Image.Image) -> tuple[np.ndarray, np.ndarray | None]:
    rgba = np.asarray(image.convert("RGBA"))
    bgr = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    alpha = rgba[:, :, 3]
    if np.any(alpha < 250):
        mask = np.where(alpha >= 16, 255, 0).astype(np.uint8)
        return bgr, mask
    return bgr, None


def _search_bounds(
    screen_width: int,
    screen_height: int,
    template_width: int,
    template_height: int,
    *,
    x0: int,
    y0: int,
    x1: int | None,
    y1: int | None,
) -> tuple[int, int, int, int] | None:
    left = max(0, x0)
    top = max(0, y0)
    max_left = x1 if x1 is not None else screen_width - template_width
    max_top = y1 if y1 is not None else screen_height - template_height
    if max_left < left or max_top < top:
        return None
    right = min(screen_width, max_left + template_width)
    bottom = min(screen_height, max_top + template_height)
    if right - left < template_width or bottom - top < template_height:
        return None
    return left, top, right, bottom


def match_score_at(screen: Image.Image, template: Image.Image, x: int, y: int) -> float:
    screen_bgr, _ = _pil_to_cv(screen)
    template_bgr, mask = _pil_to_cv(template)
    template_height, template_width = template_bgr.shape[:2]
    screen_height, screen_width = screen_bgr.shape[:2]

    if (
        x < 0
        or y < 0
        or x + template_width > screen_width
        or y + template_height > screen_height
    ):
        return 0.0

    patch = screen_bgr[y : y + template_height, x : x + template_width]
    method = MATCH_METHOD if mask is not None else MATCH_METHOD_OPAQUE
    if mask is not None:
        result = cv2.matchTemplate(patch, template_bgr, method, mask=mask)
    else:
        result = cv2.matchTemplate(patch, template_bgr, method)
    return float(result[0, 0])


def scan_best_match(
    screen: Image.Image,
    template: Image.Image,
    *,
    x0: int = 0,
    y0: int = 0,
    x1: int | None = None,
    y1: int | None = None,
    coarse_step: int = 6,
) -> TemplateMatchResult:
    del coarse_step  # OpenCV สแกนเต็ม ROI ได้เร็ว — ไม่ใช้ step แบบเดิม

    screen_bgr, _ = _pil_to_cv(screen)
    template_bgr, mask = _pil_to_cv(template)
    template_height, template_width = template_bgr.shape[:2]
    screen_height, screen_width = screen_bgr.shape[:2]

    bounds = _search_bounds(
        screen_width,
        screen_height,
        template_width,
        template_height,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
    )
    if bounds is None:
        return TemplateMatchResult(False, 0.0, x0, y0, x0, y0)

    left, top, right, bottom = bounds
    region = screen_bgr[top:bottom, left:right]
    method = MATCH_METHOD if mask is not None else MATCH_METHOD_OPAQUE

    try:
        if mask is not None:
            result = cv2.matchTemplate(region, template_bgr, method, mask=mask)
        else:
            result = cv2.matchTemplate(region, template_bgr, method)
    except cv2.error:
        return TemplateMatchResult(False, 0.0, left, top, left, top)

    _, max_score, _, max_loc = cv2.minMaxLoc(result)
    best_x = left + int(max_loc[0])
    best_y = top + int(max_loc[1])

    return TemplateMatchResult(
        found=max_score >= 0.0,
        score=float(max_score),
        x=best_x,
        y=best_y,
        expected_x=best_x,
        expected_y=best_y,
    )


def find_best_match(
    screen: Image.Image,
    template: Image.Image,
    *,
    expected_x: int,
    expected_y: int,
    search_radius: int = 48,
) -> TemplateMatchResult:
    template_width, template_height = template.size
    screen_width, screen_height = screen.size
    return scan_best_match(
        screen,
        template,
        x0=max(0, expected_x - search_radius),
        y0=max(0, expected_y - search_radius),
        x1=min(screen_width - template_width, expected_x + search_radius),
        y1=min(screen_height - template_height, expected_y + search_radius),
    )
