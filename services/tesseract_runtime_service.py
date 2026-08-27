"""ตั้งค่า Tesseract ที่ bundle มากับ AutoKey.exe — user ไม่ต้องติดตั้งเอง"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from constants.routes import ASSETS_DIR


def bundled_tesseract_dir() -> Path | None:
    candidate = ASSETS_DIR / "tesseract"
    if (candidate / "tesseract.exe").exists():
        return candidate
    return None


def configure_tesseract(custom_cmd: str = "") -> bool:
    if sys.platform != "win32":
        return False

    try:
        import pytesseract
    except ImportError:
        return False

    if custom_cmd.strip():
        pytesseract.pytesseract.tesseract_cmd = custom_cmd.strip()
        return True

    bundled = bundled_tesseract_dir()
    if bundled is not None:
        os.environ["TESSDATA_PREFIX"] = str(bundled / "tessdata")
        os.environ["PATH"] = str(bundled) + os.pathsep + os.environ.get("PATH", "")
        pytesseract.pytesseract.tesseract_cmd = str(bundled / "tesseract.exe")
        return True

    return _configure_system_tesseract(pytesseract)


def _configure_system_tesseract(pytesseract) -> bool:
    import shutil

    if shutil.which("tesseract"):
        return True

    for path in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ):
        if path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(path)
            return True

    return False


def is_tesseract_ready(custom_cmd: str = "") -> bool:
    return configure_tesseract(custom_cmd)
