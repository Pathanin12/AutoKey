from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import shutil
import sys

from constants.routes import ASSETS_DIR
from services.income_extract_service import extract_income_values

_RED_GAP = 60
_MIN_WIDTH = 2400


class IncomeOcrService:
    @staticmethod
    def read_image(path: Path) -> str:
        with TemporaryDirectory(prefix="income-ocr-") as work_dir:
            clean = _strip_red(path, Path(work_dir) / "clean.png")
            if sys.platform == "darwin":
                return _safe(_vision_text, clean)
            if sys.platform == "win32":
                return _windows_text(clean)
            return _safe(_tesseract_text, clean)


def _strip_red(path: Path, target: Path) -> Path:
    from PIL import Image, ImageChops

    with Image.open(path) as source:
        image = source.convert("RGB")
    if image.width < _MIN_WIDTH:
        ratio = _MIN_WIDTH / image.width
        image = image.resize((_MIN_WIDTH, round(image.height * ratio)), Image.LANCZOS)
    red, green, blue = image.split()
    over_green = ImageChops.subtract(red, green).point(lambda v: 255 if v > _RED_GAP else 0)
    over_blue = ImageChops.subtract(red, blue).point(lambda v: 255 if v > _RED_GAP else 0)
    image.paste((255, 255, 255), mask=ImageChops.multiply(over_green, over_blue))
    image.save(target)
    return target


def _safe(reader, path: Path) -> str:
    try:
        return reader(path) or ""
    except Exception:
        return ""


def _windows_text(path: Path) -> str:
    tess = _safe(_tesseract_text, path)
    if extract_income_values(tess):
        return tess
    win = _safe(_windows_ocr, path)
    if extract_income_values(win):
        return win
    return tess or win


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
    if not handler.performRequests_error_([request], None):
        return ""
    lines: list[str] = []
    for item in request.results() or []:
        candidates = item.topCandidates_(1)
        if candidates:
            lines.append(str(candidates[0].string()))
    return "\n".join(lines)


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
    with Image.open(path) as image:
        return pytesseract.image_to_string(image, lang="tha+eng")


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
