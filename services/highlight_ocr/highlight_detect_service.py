from __future__ import annotations

import cv2
import numpy as np

from models.highlight_bbox import HighlightBBox
from models.highlight_ocr_settings import HighlightOcrSettings


def _sample_border_pixels(lab: np.ndarray, border_px: int) -> np.ndarray:
    h, w = lab.shape[:2]
    border_px = max(4, min(border_px, min(h, w) // 4))
    strips = [
        lab[:border_px, :, :].reshape(-1, 3),
        lab[-border_px:, :, :].reshape(-1, 3),
        lab[:, :border_px, :].reshape(-1, 3),
        lab[:, -border_px:, :].reshape(-1, 3),
    ]
    return np.vstack(strips)


def _build_deviation_mask(bgr: np.ndarray, settings: HighlightOcrSettings) -> tuple[np.ndarray, float]:
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    border_pixels = _sample_border_pixels(lab, settings.border_sample_px)
    bg_median = np.median(border_pixels, axis=0)
    diff = np.linalg.norm(lab - bg_median, axis=2)

    adaptive = float(np.percentile(diff, settings.highlight_percentile))
    threshold = max(settings.min_color_distance, adaptive)
    mask = (diff >= threshold).astype(np.uint8) * 255

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    bg_v = float(np.median(_sample_border_pixels(hsv, settings.border_sample_px)[:, 2]))
    gray_highlight = (
        (hsv[:, :, 1] <= settings.max_saturation_gray)
        & (np.abs(hsv[:, :, 2].astype(np.float32) - bg_v) >= settings.min_value_delta)
    )
    mask = cv2.bitwise_or(mask, gray_highlight.astype(np.uint8) * 255)

    confidence = min(1.0, threshold / 64.0)
    return mask, confidence


def _refine_mask(mask: np.ndarray, settings: HighlightOcrSettings) -> np.ndarray:
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (settings.morph_kernel_w, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, settings.morph_kernel_v))
    refined = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_h)
    refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, kernel_v)
    refined = cv2.dilate(refined, kernel_v, iterations=1)
    return refined


def _mask_to_bboxes(mask: np.ndarray, settings: HighlightOcrSettings, base_confidence: float) -> list[HighlightBBox]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions: list[HighlightBBox] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < settings.min_region_width or h < settings.min_region_height:
            continue
        area_ratio = (w * h) / max(1, mask.shape[0] * mask.shape[1])
        confidence = min(1.0, base_confidence + area_ratio * 4.0)
        if confidence < settings.min_detection_confidence:
            continue
        regions.append(HighlightBBox(x, y, w, h, confidence))

    regions.sort(key=lambda item: (item.y, item.x))
    return _merge_vertical_regions(regions)


def _merge_vertical_regions(regions: list[HighlightBBox]) -> list[HighlightBBox]:
    if not regions:
        return []

    merged: list[HighlightBBox] = []
    current = regions[0]
    for region in regions[1:]:
        vertical_gap = region.y - current.y1
        horizontal_overlap = min(current.x1, region.x1) - max(current.x, region.x)
        if vertical_gap <= max(8, current.height // 2) and horizontal_overlap > 0:
            x0 = min(current.x, region.x)
            y0 = min(current.y, region.y)
            x1 = max(current.x1, region.x1)
            y1 = max(current.y1, region.y1)
            confidence = max(current.confidence, region.confidence)
            current = HighlightBBox(x0, y0, x1 - x0, y1 - y0, confidence)
            continue
        merged.append(current)
        current = region
    merged.append(current)
    return merged


def detect_highlight(bgr: np.ndarray, settings: HighlightOcrSettings) -> tuple[list[HighlightBBox], np.ndarray, float]:
    mask, confidence = _build_deviation_mask(bgr, settings)
    refined = _refine_mask(mask, settings)
    regions = _mask_to_bboxes(refined, settings, confidence)
    return regions, refined, confidence


def get_highlight_bbox(
    bgr: np.ndarray,
    settings: HighlightOcrSettings,
) -> tuple[list[HighlightBBox], np.ndarray, float]:
    regions, mask, confidence = detect_highlight(bgr, settings)
    h, w = bgr.shape[:2]
    scale = max(1, int(round(settings.line_expand_y_px)))
    pad_x = max(0, int(round(settings.line_expand_x_px)))

    expanded: list[HighlightBBox] = []
    for region in regions:
        pad_y = max(scale, region.height // 4)
        expanded.append(region.expand(pad_x=pad_x, pad_y=pad_y, max_w=w, max_h=h))

    expanded.sort(key=lambda item: (item.y, item.x))
    return expanded, mask, confidence
