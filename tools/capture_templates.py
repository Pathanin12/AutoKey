"""(เลิกใช้แล้ว) เคย crop ปุ่มสำหรับ OpenCV — ระบบใช้คีย์บอร์ดเท่านั้นแล้ว"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from constants.routes import TEMPLATES_DIR


TEMPLATE_HINTS = {
    "pv_new.png": "ปุ่ม New ใน PV toolbar",
    "pv_save.png": "ปุ่ม Save ใน PV toolbar",
    "btn_ok.png": "ปุ่ม ตกลง",
    "btn_cancel.png": "ปุ่ม ยกเลิก",
    "btn_search.png": "ปุ่มแว่นขยาย",
    "wt_dialog.png": "หัวข้อ dialog ภาษีหัก ณ ที่จ่าย",
    "tax_invoice_dialog.png": "หัวข้อ dialog ใบกำกับภาษีซื้อ",
}


def main() -> None:
    try:
        import pyautogui
    except ImportError as exc:
        raise SystemExit("ติดตั้ง requirements.txt ก่อน") from exc

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    print("AutoKey Template Capture")
    print(f"บันทึกไปที่: {TEMPLATES_DIR}")
    print("กด Ctrl+C เพื่อออก\n")

    for filename, hint in TEMPLATE_HINTS.items():
        input(f"[Enter] จับภาพ {filename} — {hint}")
        print("เลื่อนเมาส์ไปมุมซ้ายบนของปุ่ม แล้วกด Enter")
        input("...")
        x1, y1 = pyautogui.position()
        print("เลื่อนเมาส์ไปมุมขวาล่างของปุ่ม แล้วกด Enter")
        input("...")
        x2, y2 = pyautogui.position()

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        image = pyautogui.screenshot(region=(left, top, width, height))
        output = TEMPLATES_DIR / filename
        image.save(output)
        print(f"saved: {output}\n")


if __name__ == "__main__":
    main()
