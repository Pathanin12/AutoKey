from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys

from constants.routes import ASSETS_DIR
from services.income_extract_service import extract_income_values


class IncomeOcrService:
    @staticmethod
    def read_image(path: Path) -> str:
        if sys.platform == "darwin":
            return _vision_text(path)
        if sys.platform == "win32":
            return _windows_text(path)
        return ""


def _vision_text(path: Path) -> str:
    from Foundation import NSData
    from Vision import VNImageRequestHandler, VNRecognizeTextRequest

    data = NSData.dataWithContentsOfFile_(str(path))
    if data is None:
        return ""
    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(0)
    request.setUsesLanguageCorrection_(True)
    try:
        request.setRecognitionLanguages_(["th-TH", "en-US"])
    except Exception:
        pass
    handler = VNImageRequestHandler.alloc().initWithData_options_(data, None)
    ok = handler.performRequests_error_([request], None)
    if not ok:
        return ""
    lines: list[str] = []
    for item in request.results() or []:
        candidates = item.topCandidates_(1)
        if candidates:
            lines.append(str(candidates[0].string()))
    return "\n".join(lines)


def _windows_text(path: Path) -> str:
    tess = _safe(_tesseract_text, path)
    if extract_income_values(tess):
        return tess
    win = _safe(_windows_ocr, path)
    if extract_income_values(win):
        return win
    return tess or win


def _safe(reader, path: Path) -> str:
    try:
        return reader(path) or ""
    except Exception:
        return ""


def _windows_ocr(path: Path) -> str:
    import asyncio

    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    async def recognize() -> str:
        engine = None
        for tag in ("th-TH", "th"):
            language = Language(tag)
            if OcrEngine.is_language_supported(language):
                engine = OcrEngine.try_create_from_language(language)
                if engine:
                    break
        if engine is None:
            engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            return ""
        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream)
        writer.write_bytes(list(path.read_bytes()))
        await writer.store_async()
        stream.seek(0)
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        if result is None:
            return ""
        return "\n".join(line.text for line in result.lines or [])

    return asyncio.run(recognize())


def _tesseract_text(path: Path) -> str:
    import pytesseract
    from PIL import Image

    cmd = _tesseract_cmd()
    if not cmd:
        return ""
    pytesseract.pytesseract.tesseract_cmd = cmd
    tessdata = Path(cmd).with_name("tessdata")
    if tessdata.is_dir():
        os.environ["TESSDATA_PREFIX"] = str(tessdata)
    return pytesseract.image_to_string(Image.open(path), lang="tha+eng")


def _tesseract_cmd() -> str:
    bundled = ASSETS_DIR / "tesseract" / "tesseract.exe"
    if bundled.exists():
        return str(bundled)
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ):
        if candidate.exists():
            return str(candidate)
    return ""
