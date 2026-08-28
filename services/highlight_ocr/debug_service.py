from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from models.highlight_bbox import HighlightBBox
from models.ocr_word_result import OcrLineResult, OcrWordResult


def _load_font(size: int = 16) -> ImageFont.ImageFont:
    for name in ("Tahoma.ttf", "Arial Unicode.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_highlight_debug(
    image: Image.Image,
    highlight_regions: list[HighlightBBox],
    lines: list[OcrLineResult],
    *,
    mask: Image.Image | None = None,
) -> Image.Image:
    canvas = image.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font()

    for region in highlight_regions:
        draw.rectangle(
            (region.x, region.y, region.x1, region.y1),
            outline=(255, 64, 64, 255),
            width=3,
        )
        draw.text((region.x + 4, max(0, region.y - 18)), f"H {region.confidence:.0%}", fill=(255, 64, 64, 255), font=font)

    for line in lines:
        draw.rectangle(
            (line.bbox.x, line.bbox.y, line.bbox.x1, line.bbox.y1),
            outline=(64, 255, 64, 255),
            width=2,
        )
        label = f"OCR {line.confidence:.0%}: {line.text[:40]}"
        draw.text((line.bbox.x + 4, line.bbox.y1 + 2), label, fill=(64, 255, 64, 255), font=font)

        for word in line.words:
            draw.rectangle(
                (word.bbox.x, word.bbox.y, word.bbox.x1, word.bbox.y1),
                outline=(64, 128, 255, 200),
                width=1,
            )

    merged = Image.alpha_composite(canvas, overlay)
    if mask is not None:
        mask_rgb = mask.convert("RGB").resize(merged.size, Image.Resampling.NEAREST)
        preview = Image.new("RGB", (merged.width * 2, merged.height), (20, 20, 20))
        preview.paste(merged.convert("RGB"), (0, 0))
        preview.paste(mask_rgb, (merged.width, 0))
        return preview
    return merged.convert("RGB")


def save_debug_bundle(
    debug_dir,
    *,
    original: Image.Image,
    highlight_detected: Image.Image,
    cropped: Image.Image | None,
    preprocessed: Image.Image | None,
    ocr_result: Image.Image,
) -> None:
    from pathlib import Path

    path = Path(debug_dir)
    path.mkdir(parents=True, exist_ok=True)
    original.save(path / "original.png")
    highlight_detected.save(path / "highlight_detected.png")
    if cropped is not None:
        cropped.save(path / "cropped.png")
    if preprocessed is not None:
        preprocessed.save(path / "preprocessed.png")
    ocr_result.save(path / "ocr_result.png")
