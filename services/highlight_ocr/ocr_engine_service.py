from __future__ import annotations

from PIL import Image

from models.highlight_bbox import HighlightBBox
from models.highlight_ocr_settings import HighlightOcrSettings
from models.ocr_word_result import OcrWordResult
from services.tesseract_runtime_service import configure_tesseract


def run_ocr(
    image: Image.Image,
    settings: HighlightOcrSettings,
    *,
    offset_x: int = 0,
    offset_y: int = 0,
) -> list[OcrWordResult]:
    engine = settings.primary_engine.lower().strip()
    if engine == "auto":
        return _run_auto(image, settings, offset_x=offset_x, offset_y=offset_y)
    if engine == "paddleocr":
        return _run_paddleocr(image, settings, offset_x=offset_x, offset_y=offset_y)
    if engine == "easyocr":
        return _run_easyocr(image, settings, offset_x=offset_x, offset_y=offset_y)
    return _run_tesseract(image, settings, offset_x=offset_x, offset_y=offset_y)


def _run_auto(
    image: Image.Image,
    settings: HighlightOcrSettings,
    *,
    offset_x: int,
    offset_y: int,
) -> list[OcrWordResult]:
    candidates: list[tuple[float, list[OcrWordResult], str]] = []
    for engine_name, runner in (
        ("paddleocr", _run_paddleocr),
        ("easyocr", _run_easyocr),
        ("tesseract", _run_tesseract),
    ):
        words = runner(image, settings, offset_x=offset_x, offset_y=offset_y)
        if not words:
            continue
        score = sum(word.confidence for word in words) / len(words)
        candidates.append((score, words, engine_name))

    if not candidates:
        return []

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _run_tesseract(
    image: Image.Image,
    settings: HighlightOcrSettings,
    *,
    offset_x: int,
    offset_y: int,
) -> list[OcrWordResult]:
    try:
        import pytesseract
    except ImportError:
        return []

    if not configure_tesseract(settings.tesseract_cmd):
        return []

    langs = _lang_candidates(settings.lang, tesseract=True)
    best_words: list[OcrWordResult] = []

    for lang in langs:
        for psm in settings.tesseract_psm_modes:
            config = f"--psm {psm} --oem 1 -c preserve_interword_spaces=1"
            try:
                data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
            except Exception:
                continue

            words = _parse_tesseract_data(data, offset_x, offset_y, engine="tesseract")
            if words and (not best_words or _avg_conf(words) >= _avg_conf(best_words)):
                best_words = words

    return best_words


def _parse_tesseract_data(data, offset_x: int, offset_y: int, *, engine: str) -> list[OcrWordResult]:
    words: list[OcrWordResult] = []
    count = len(data.get("text", []))
    for index in range(count):
        text = str(data["text"][index]).strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][index])
        except (TypeError, ValueError):
            conf = 0.0
        if conf < 0:
            continue
        x = int(data["left"][index]) + offset_x
        y = int(data["top"][index]) + offset_y
        w = int(data["width"][index])
        h = int(data["height"][index])
        words.append(
            OcrWordResult(
                text=text,
                bbox=HighlightBBox(x, y, max(1, w), max(1, h), conf / 100.0),
                confidence=max(0.0, conf / 100.0),
                engine=engine,
            )
        )
    return words


def _run_easyocr(
    image: Image.Image,
    settings: HighlightOcrSettings,
    *,
    offset_x: int,
    offset_y: int,
) -> list[OcrWordResult]:
    try:
        import easyocr
        import numpy as np
    except ImportError:
        return []

    langs = _lang_candidates(settings.lang, tesseract=False)
    reader = easyocr.Reader(langs, gpu=False, verbose=False)
    results = reader.readtext(np.asarray(image.convert("RGB")))

    words: list[OcrWordResult] = []
    for bbox_points, text, confidence in results:
        text = str(text).strip()
        if not text:
            continue
        xs = [point[0] for point in bbox_points]
        ys = [point[1] for point in bbox_points]
        x0 = int(min(xs)) + offset_x
        y0 = int(min(ys)) + offset_y
        x1 = int(max(xs)) + offset_x
        y1 = int(max(ys)) + offset_y
        words.append(
            OcrWordResult(
                text=text,
                bbox=HighlightBBox(x0, y0, max(1, x1 - x0), max(1, y1 - y0), float(confidence)),
                confidence=float(confidence),
                engine="easyocr",
            )
        )
    return words


def _run_paddleocr(
    image: Image.Image,
    settings: HighlightOcrSettings,
    *,
    offset_x: int,
    offset_y: int,
) -> list[OcrWordResult]:
    try:
        import numpy as np
        from paddleocr import PaddleOCR
    except ImportError:
        return []

    lang = "th" if settings.lang.lower().startswith("th") else settings.lang
    ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    results = ocr.ocr(np.asarray(image.convert("RGB")), cls=True)

    words: list[OcrWordResult] = []
    for block in results or []:
        for item in block or []:
            bbox_points, payload = item
            text, confidence = payload
            text = str(text).strip()
            if not text:
                continue
            xs = [point[0] for point in bbox_points]
            ys = [point[1] for point in bbox_points]
            x0 = int(min(xs)) + offset_x
            y0 = int(min(ys)) + offset_y
            x1 = int(max(xs)) + offset_x
            y1 = int(max(ys)) + offset_y
            words.append(
                OcrWordResult(
                    text=text,
                    bbox=HighlightBBox(x0, y0, max(1, x1 - x0), max(1, y1 - y0), float(confidence)),
                    confidence=float(confidence),
                    engine="paddleocr",
                )
            )
    return words


def _lang_candidates(lang: str, *, tesseract: bool) -> list[str]:
    primary = lang.strip() or "th"
    if tesseract:
        options = [primary]
        if primary != "tha":
            options.append("tha")
        return list(dict.fromkeys(options))

    mapping = {"tha": "th", "th": "th", "eng": "en", "en": "en"}
    mapped = mapping.get(primary.lower(), primary.lower())
    options = [mapped]
    if mapped != "th":
        options.append("th")
    return list(dict.fromkeys(options))


def _avg_conf(words: list[OcrWordResult]) -> float:
    if not words:
        return 0.0
    return sum(word.confidence for word in words) / len(words)
