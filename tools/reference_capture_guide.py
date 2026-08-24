#!/usr/bin/env python3
"""แสดงรายการรูปที่ต้องถ่ายบน Windows สำหรับ flow preview / templates"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from constants.reference_images import CAPTURE_CHECKLIST, capture_instructions, reference_path
from PIL import Image


def main() -> None:
    print("\n".join(capture_instructions()))
    print("\n--- สถานะไฟล์ ---")
    for item in CAPTURE_CHECKLIST:
        path = item.path
        if not path.exists():
            print(f"✗ {item.filename}: ไม่พบ — {item.label}")
            continue
        w, h = Image.open(path).size
        ok = "✓" if w >= 1920 and h >= 1080 else "~"
        print(f"{ok} {item.filename} ({w}×{h}) — {item.label}")


if __name__ == "__main__":
    main()
