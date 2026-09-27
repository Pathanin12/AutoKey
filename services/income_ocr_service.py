from __future__ import annotations

from pathlib import Path
import sys


class IncomeOcrService:
    @staticmethod
    def read_image(path: Path) -> str:
        if sys.platform == "darwin":
            return _vision_text(path)
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
