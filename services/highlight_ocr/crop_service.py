from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from models.highlight_bbox import HighlightBBox


def crop_highlight_region(bgr: np.ndarray, bbox: HighlightBBox) -> np.ndarray:
    x0, y0, x1, y1 = bbox.x, bbox.y, bbox.x1, bbox.y1
    return bgr[y0:y1, x0:x1].copy()


def crop_regions(bgr: np.ndarray, bboxes: list[HighlightBBox]) -> list[np.ndarray]:
    return [crop_highlight_region(bgr, bbox) for bbox in bboxes]
