#!/usr/bin/env python3
"""Demo: อ่านข้อความไทยจาก Highlight บนหน้าจอ (ไม่ใช้ Clipboard)"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.highlight_ocr_settings import HighlightOcrSettings
from services.highlight_ocr.highlight_ocr_service import get_selected_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Highlight OCR — อ่านข้อความไทยจาก selection บนหน้าจอ")
    parser.add_argument("--delay", type=float, default=3.0, help="วินาทีรอก่อนจับภาพ (ให้เวลา highlight ข้อความ)")
    parser.add_argument("--engine", default="auto", choices=["auto", "tesseract", "easyocr", "paddleocr"])
    parser.add_argument("--debug", action="store_true", help="บันทึก debug images")
    parser.add_argument("--debug-dir", default="debug/highlight_ocr")
    parser.add_argument("--min-color-distance", type=float, default=12.0, help="threshold LAB จากพื้นหลัง")
    parser.add_argument("--highlight-percentile", type=float, default=97.5, help="percentile ของความต่างสี")
    parser.add_argument("--line-expand-y", type=int, default=6, help="ขยาย bbox แนวตั้ง (px)")
    parser.add_argument("--upscale", type=float, default=3.0, help="ขยายภาพก่อน OCR")
    parser.add_argument("--json", action="store_true", help="พิมพ์ผลเป็น JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.delay > 0:
        print(f"Highlight ข้อความบนหน้าจอภายใน {args.delay:.0f} วินาที...")
        time.sleep(args.delay)

    settings = HighlightOcrSettings(
        primary_engine=args.engine,
        debug=args.debug,
        debug_dir=Path(args.debug_dir),
        min_color_distance=args.min_color_distance,
        highlight_percentile=args.highlight_percentile,
        line_expand_y_px=args.line_expand_y,
        upscale_factor=args.upscale,
    )

    result = get_selected_text(settings)

    if args.json:
        payload = {
            "text": result.text,
            "engine": result.engine_used,
            "dpi_scale": result.dpi_scale,
            "average_confidence": result.average_confidence,
            "lines": [
                {
                    "text": line.text,
                    "confidence": line.confidence,
                    "engine": line.engine,
                    "bbox": line.bbox.as_tuple(),
                }
                for line in result.lines
            ],
            "highlight_regions": [region.as_tuple() for region in result.highlight_regions],
            "debug_dir": result.debug_dir,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result.text else 1

    print("=" * 60)
    print(f"DPI scale: {result.dpi_scale:.2f}")
    print(f"Engine: {result.engine_used}")
    print(f"Highlight regions: {len(result.highlight_regions)}")
    print(f"Confidence: {result.average_confidence:.0%}")
    if result.debug_dir:
        print(f"Debug: {result.debug_dir}")
    print("-" * 60)
    if result.text:
        print(result.text)
    else:
        print("(ไม่พบข้อความ — ลองเปิด --debug และปรับ threshold)")
    print("=" * 60)
    return 0 if result.text else 1


if __name__ == "__main__":
    raise SystemExit(main())
