"""พิกัด highlight ตาม phase — โฟล์แรก/สุดท้าย (step 0/10) ดู constants/flow_model.py"""

from __future__ import annotations

from models.screen_region import ScreenRegion

STEP_REGIONS: dict[int, ScreenRegion] = {
    0: ScreenRegion(120, 80, 980, 520, "Dialog เลือกบริษัท / ฐานข้อมูล"),
    1: ScreenRegion(0, 24, 960, 36, "เมนู 5.บัญชี > 1.ลงประจำวัน > 2.สมุดรายวันจ่าย"),
    2: ScreenRegion(24, 72, 420, 48, "ปุ่ม New / สร้างรายการ"),
    3: ScreenRegion(48, 132, 760, 96, "วันที่ / รายละเอียด"),
    4: ScreenRegion(48, 248, 920, 72, "ตาราง — บัญชีค่าบริการ 5330-05"),
    5: ScreenRegion(48, 320, 920, 72, "ตาราง — บัญชีภาษีซื้อ 1154-00"),
    6: ScreenRegion(360, 120, 640, 520, "Dialog ใบกำกับภาษีซื้อ"),
    7: ScreenRegion(360, 100, 640, 540, "Dialog ภาษีหัก ณ ที่จ่าย"),
    8: ScreenRegion(48, 392, 920, 72, "ตาราง — บัญชีเงินสด 1111-00"),
    9: ScreenRegion(24, 72, 420, 48, "ปุ่ม Save / บันทึก"),
    10: ScreenRegion(120, 80, 980, 520, "Dialog เลือกบริษัท — เปลี่ยนบริษัท"),
}


def get_step_region(step_index: int) -> ScreenRegion | None:
    return STEP_REGIONS.get(step_index)
