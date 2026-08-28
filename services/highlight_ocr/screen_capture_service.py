from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class ScreenCapture:
    image: Image.Image
    bgr: np.ndarray
    dpi_scale: float
    logical_size: tuple[int, int]


def get_dpi_scale() -> float:
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes

        user32 = ctypes.windll.user32
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
        hdc = user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        user32.ReleaseDC(0, hdc)
        if dpi <= 0:
            return 1.0
        return dpi / 96.0
    except Exception:
        return 1.0


def capture_screen(
    *,
    target_logical_width: int | None = None,
    target_logical_height: int | None = None,
) -> ScreenCapture:
    import cv2

    dpi_scale = get_dpi_scale()

    try:
        import pyautogui

        shot = pyautogui.screenshot()
    except Exception as exc:
        raise RuntimeError("ต้องติดตั้ง pyautogui และรันบน Windows/macOS ที่มีหน้าจอ") from exc

    image = shot.convert("RGBA")
    logical_w, logical_h = image.size

    if target_logical_width and target_logical_height:
        if image.size != (target_logical_width, target_logical_height):
            image = image.resize((target_logical_width, target_logical_height), Image.Resampling.LANCZOS)
            logical_w, logical_h = target_logical_width, target_logical_height

    rgb = np.asarray(image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    return ScreenCapture(
        image=image,
        bgr=bgr,
        dpi_scale=dpi_scale,
        logical_size=(logical_w, logical_h),
    )
