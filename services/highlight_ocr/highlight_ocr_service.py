"""OCR อ่านข้อความจาก Highlight บนหน้าจอ — Computer Vision + OCR (local)"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from models.highlight_bbox import HighlightBBox
from models.highlight_ocr_result import HighlightOcrResult
from models.highlight_ocr_settings import HighlightOcrSettings
from models.ocr_word_result import OcrLineResult
from services.highlight_ocr.crop_service import crop_highlight_region
from services.highlight_ocr.debug_service import draw_highlight_debug, save_debug_bundle
from services.highlight_ocr.filter_service import filter_ocr_by_bbox, merge_lines, words_to_line
from services.highlight_ocr.highlight_detect_service import detect_highlight, get_highlight_bbox
from services.highlight_ocr.ocr_engine_service import run_ocr
from services.highlight_ocr.preprocess_service import preprocess_image
from services.highlight_ocr.screen_capture_service import ScreenCapture, capture_screen


def get_selected_text(settings: HighlightOcrSettings | None = None) -> HighlightOcrResult:
    settings = settings or HighlightOcrSettings()
    capture = capture_screen(
        target_logical_width=settings.target_logical_width,
        target_logical_height=settings.target_logical_height,
    )
    return get_selected_text_from_capture(capture, settings)


def get_selected_text_from_capture(
    capture: ScreenCapture,
    settings: HighlightOcrSettings,
) -> HighlightOcrResult:
    highlight_regions, mask, _det_conf = get_highlight_bbox(capture.bgr, settings)
    if not highlight_regions:
        return _empty_result(capture, settings, highlight_regions)

    lines: list[OcrLineResult] = []
    engine_used = settings.primary_engine
    debug_crops: list[Image.Image] = []
    debug_preprocessed: list[Image.Image] = []

    for region in highlight_regions:
        cropped_bgr = crop_highlight_region(capture.bgr, region)
        if cropped_bgr.size == 0:
            continue

        best_line: OcrLineResult | None = None
        for variant_name, prepared in preprocess_image(cropped_bgr, settings):
            words = run_ocr(prepared, settings)
            words = _map_words_to_screen(words, region, settings)
            filtered = filter_ocr_by_bbox(words, region, padding=settings.ocr_bbox_padding)
            filtered = [word for word in filtered if word.confidence >= settings.min_ocr_confidence]
            line = words_to_line(filtered, region, engine=settings.primary_engine)
            if filtered:
                line = OcrLineResult(
                    text=line.text,
                    bbox=line.bbox,
                    confidence=line.confidence,
                    words=line.words,
                    engine=filtered[0].engine,
                )

            if line.text and (best_line is None or line.confidence > best_line.confidence):
                best_line = line
                engine_used = line.engine
                if settings.debug:
                    debug_preprocessed.append(prepared)

        if best_line and best_line.text:
            lines.append(best_line)

        if settings.debug:
            rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
            debug_crops.append(Image.fromarray(rgb))

    text = merge_lines(lines)
    debug_dir: str | None = None
    if settings.debug:
        debug_dir = str(settings.debug_dir)
        _save_debug_outputs(
            capture,
            settings,
            highlight_regions,
            lines,
            mask,
            debug_crops,
            debug_preprocessed,
        )

    return HighlightOcrResult(
        text=text,
        lines=tuple(lines),
        highlight_regions=tuple(highlight_regions),
        dpi_scale=capture.dpi_scale,
        engine_used=engine_used,
        debug_dir=debug_dir,
    )


def _empty_result(
    capture: ScreenCapture,
    settings: HighlightOcrSettings,
    highlight_regions: list[HighlightBBox],
) -> HighlightOcrResult:
    debug_dir: str | None = None
    if settings.debug:
        debug_dir = str(settings.debug_dir)
        settings.debug_dir.mkdir(parents=True, exist_ok=True)
        capture.image.save(settings.debug_dir / "original.png")
        regions, mask, _ = detect_highlight(capture.bgr, settings)
        mask_img = Image.fromarray(mask)
        debug_img = draw_highlight_debug(capture.image, regions, [], mask=mask_img)
        debug_img.save(settings.debug_dir / "highlight_detected.png")
        Image.new("RGB", (32, 32), (30, 30, 30)).save(settings.debug_dir / "cropped.png")
        Image.new("RGB", (32, 32), (30, 30, 30)).save(settings.debug_dir / "preprocessed.png")
        debug_img.save(settings.debug_dir / "ocr_result.png")

    return HighlightOcrResult(
        text="",
        lines=tuple(),
        highlight_regions=tuple(highlight_regions),
        dpi_scale=capture.dpi_scale,
        engine_used=settings.primary_engine,
        debug_dir=debug_dir,
    )


def _map_words_to_screen(
    words: list,
    region: HighlightBBox,
    settings: HighlightOcrSettings,
):
    from models.ocr_word_result import OcrWordResult

    scale = max(1.0, settings.upscale_factor)
    border = 12
    mapped: list[OcrWordResult] = []
    for word in words:
        x = int((word.bbox.x - border) / scale) + region.x
        y = int((word.bbox.y - border) / scale) + region.y
        w = max(1, int(word.bbox.width / scale))
        h = max(1, int(word.bbox.height / scale))
        mapped.append(
            OcrWordResult(
                text=word.text,
                bbox=HighlightBBox(x, y, w, h, word.confidence),
                confidence=word.confidence,
                engine=word.engine,
            )
        )
    return mapped


def _save_debug_outputs(
    capture: ScreenCapture,
    settings: HighlightOcrSettings,
    highlight_regions: list[HighlightBBox],
    lines: list[OcrLineResult],
    mask: np.ndarray,
    debug_crops: list[Image.Image],
    debug_preprocessed: list[Image.Image],
) -> None:
    mask_img = Image.fromarray(mask)
    debug_img = draw_highlight_debug(capture.image, highlight_regions, lines, mask=mask_img)
    cropped = _stack_images(debug_crops) if debug_crops else None
    preprocessed = _stack_images(debug_preprocessed) if debug_preprocessed else None
    save_debug_bundle(
        settings.debug_dir,
        original=capture.image.convert("RGB"),
        highlight_detected=debug_img,
        cropped=cropped,
        preprocessed=preprocessed,
        ocr_result=debug_img,
    )


def _stack_images(images: list[Image.Image]) -> Image.Image | None:
    if not images:
        return None
    width = max(image.width for image in images)
    height = sum(image.height for image in images)
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    y = 0
    for image in images:
        canvas.paste(image.convert("RGB"), (0, y))
        y += image.height
    return canvas
