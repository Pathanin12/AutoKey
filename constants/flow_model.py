"""แหล่งความจริงของลำดับ Flow — โฟล์ 1 ค้นหาใน dialog → PV → โฟล์สุดท้าย กด 8"""

from __future__ import annotations

from dataclasses import dataclass

from constants.routes import MENU_OTHERS, MENU_OTHERS_CHANGE_COMPANY

FLOW_1_LABEL = "โฟล์แรก — เลือกบริษัท"
FLOW_1_END_LABEL = "โฟล์สุดท้าย — เปลี่ยนบริษัท"
FLOW_2_LABEL = "โฟล์ 2 — สมุดรายวันจ่าย (PV)"

FULL_SEQUENCE_NOTE = "โฟล์ 1 เลือก DB → PV ทุกแถว (F8=เจ้าหนี้, F10=ภาษีซื้อ) → จบ"

PHASE_FLOW_1_START = 0
PHASE_FLOW_2_OPEN = 1
PHASE_FLOW_2_NEW = 2
PHASE_FLOW_2_HEADER = 3
PHASE_FLOW_2_SERVICE = 4
PHASE_FLOW_2_VAT = 5
PHASE_FLOW_2_TAX_DIALOG = 6
PHASE_FLOW_2_WT_DIALOG = 7
PHASE_FLOW_2_CASH = 8
PHASE_FLOW_2_SAVE = 9
PHASE_FLOW_1_END = 10

PHASE_TITLES: dict[int, str] = {
    PHASE_FLOW_1_START: f"{FLOW_1_LABEL} (dialog เลือกข้อมูล — ไม่กด 8)",
    PHASE_FLOW_2_OPEN: f"{FLOW_2_LABEL} — เปิด (5→1→2)",
    PHASE_FLOW_2_NEW: f"{FLOW_2_LABEL} — สร้างรายการ (F2)",
    PHASE_FLOW_2_HEADER: f"{FLOW_2_LABEL} — กรอกหัวเรื่อง",
    PHASE_FLOW_2_SERVICE: f"{FLOW_2_LABEL} — 5330-05",
    PHASE_FLOW_2_VAT: f"{FLOW_2_LABEL} — 1154-00",
    PHASE_FLOW_2_TAX_DIALOG: f"{FLOW_2_LABEL} — Dialog ใบกำกับ",
    PHASE_FLOW_2_WT_DIALOG: f"{FLOW_2_LABEL} — Dialog WT (ยกเลิก)",
    PHASE_FLOW_2_CASH: f"{FLOW_2_LABEL} — 1111-00",
    PHASE_FLOW_2_SAVE: f"{FLOW_2_LABEL} — F10 + ยืนยันภาษีซื้อ",
    PHASE_FLOW_1_END: f"{FLOW_1_END_LABEL} (กด {MENU_OTHERS}→{MENU_OTHERS_CHANGE_COMPANY})",
}

STEP_REGION_FLOW_1_START = 0
STEP_REGION_FLOW_1_END = 10

FLOW_1_SEARCH_ENTER_COUNT = 2


@dataclass(frozen=True)
class FlowStepSpec:
    step_no: int
    kind: str
    label: str
    value: str = ""
    note: str = ""


FLOW_1_START_DETAIL: tuple[FlowStepSpec, ...] = (
    FlowStepSpec(1, "tab", "Tab → ปุ่ม ค้นหา", note="Tab ×2 (lookup_search.button_tabs)"),
    FlowStepSpec(2, "enter", "Enter → เปิดช่องค้นหา", note="แทนคลิกปุ่ม ค้นหา"),
    FlowStepSpec(3, "type", "พิมพ์ชื่อบริษัท", note="จากฟอร์ม AutoKey"),
    FlowStepSpec(4, "enter", "Enter ครั้งที่ 1", note="เลือกรายการ"),
    FlowStepSpec(5, "enter", "Enter ครั้งที่ 2", note="ยืนยัน → เข้าเมนูหลัก"),
)

FLOW_1_END_DETAIL: tuple[FlowStepSpec, ...] = (
    FlowStepSpec(1, "key", "กด 8. อื่นๆ", MENU_OTHERS, "หลังจบ PV — อยู่เมนูหลัก"),
    FlowStepSpec(
        2,
        "key",
        "กด 8. เปลี่ยนบริษัท",
        MENU_OTHERS_CHANGE_COMPANY,
        "เปิด dialog เลือกข้อมูล (Shift+F11)",
    ),
)

FLOW_1_STEPS_START: tuple[str, ...] = tuple(
    f"{s.step_no}. {s.label}" + (f" → {s.value}" if s.value else "") for s in FLOW_1_START_DETAIL
)
FLOW_1_STEPS_END: tuple[str, ...] = tuple(
    f"{s.step_no}. {s.label}" + (f" → {s.value}" if s.value else "") for s in FLOW_1_END_DETAIL
)
