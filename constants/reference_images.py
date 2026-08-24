"""รูปอ้างอิง Express — 1 รูปต่อ 1 หน้าจอ (1920×1080 ใน assets/reference/)"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.routes import REFERENCE_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass(frozen=True)
class ReferenceScreen:
    screen_id: str
    filename: str
    label: str
    when_used: str

    @property
    def path(self) -> Path:
        return REFERENCE_DIR / self.filename


CAPTURE_CHECKLIST: tuple[ReferenceScreen, ...] = (
    ReferenceScreen(
        "01_menu_open_pv",
        "7.png",
        "เมนู 5→1→2 (สมุดรายวันจ่าย)",
        "เปิด 5.บัญชี → 1.ลงประจำวัน → เห็น 2.สมุดรายวันจ่าย",
    ),
    ReferenceScreen(
        "02_pv_empty",
        "11.png",
        "หน้า PV เปิด",
        "หลังกด 2.สมุดรายวันจ่าย — ฟอร์ม PV",
    ),
    ReferenceScreen(
        "03_pv_header",
        "9.png",
        "PV สร้างรายการ / แถวว่าง",
        "F2 สร้างรายการ — ช่องวันที่ รายละเอียด ตาราง",
    ),
    ReferenceScreen(
        "04_pv_grid",
        "12.png",
        "PV กรอกแถวบัญชี",
        "5330-05 / 1154-00 / 1111-00",
    ),
    ReferenceScreen(
        "05_tax_dialog",
        "13.png",
        "Dialog ใบกำกับภาษีซื้อ",
        "หลัง Enter แถว 1154-00",
    ),
    ReferenceScreen(
        "06_wt_dialog",
        "14.png",
        "Dialog ภาษีหัก ณ ที่จ่าย",
        "หลัง ตกลง ใบกำกับ — กด ยกเลิก",
    ),
    ReferenceScreen(
        "07_menu_end",
        "15.png",
        "เมนู 8→8 เปลี่ยนบริษัท",
        "จบ PV — 8.อื่นๆ → 8.เปลี่ยนบริษัท",
    ),
    ReferenceScreen(
        "08_company_select",
        "2.png",
        "Dialog เลือกข้อมูล",
        "(อ้างอิง) หน้าเลือกบริษัท / ฐานข้อมูล",
    ),
)

IMAGE_KEY_TO_SCREEN: dict[str, str] = {
    "menu_open_pv": "01_menu_open_pv",
    "pv_main": "02_pv_empty",
    "pv_header": "03_pv_header",
    "pv_grid": "04_pv_grid",
    "tax_dialog": "05_tax_dialog",
    "wt_dialog": "06_wt_dialog",
    "menu_end": "07_menu_end",
    "company_select": "08_company_select",
}

_SCREEN_BY_ID: dict[str, ReferenceScreen] = {item.screen_id: item for item in CAPTURE_CHECKLIST}


def reference_path(image_key: str, *, fallback: str = "pv_main") -> Path:
    screen_id = IMAGE_KEY_TO_SCREEN.get(image_key, IMAGE_KEY_TO_SCREEN.get(fallback, "02_pv_empty"))
    screen = _SCREEN_BY_ID[screen_id]
    return screen.path


def capture_instructions() -> list[str]:
    lines = [
        f"ถ่าย PNG ทั้งจอ {SCREEN_WIDTH}×{SCREEN_HEIGHT} (scale 100%) — ไม่ crop ไม่บีบอัด",
        f"วางไฟล์ใน {REFERENCE_DIR}",
        "",
    ]
    for index, item in enumerate(CAPTURE_CHECKLIST, start=1):
        lines.append(f"{index}. {item.filename} — {item.label}")
        lines.append(f"   {item.when_used}")
    return lines
