from __future__ import annotations

from pathlib import Path
import sys


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
    try:
        return _windows_ocr(path)
    except Exception:
        return ""


def _windows_ocr(path: Path) -> str:
    import asyncio

    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage import FileAccessMode, StorageFile

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
        file = await StorageFile.get_file_from_path_async(str(path))
        stream = await file.open_async(FileAccessMode.READ)
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        if result is None:
            return ""
        return "\n".join(line.text for line in result.lines or [])

    return asyncio.run(recognize())
