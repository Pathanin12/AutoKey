"""แหล่งความจริงของลำดับ Flow — บริษัทเดียว: เปิด PV แล้วทำทุกแถว"""

from __future__ import annotations

from dataclasses import dataclass

from constants.routes import MENU_OTHERS

FLOW_1_LABEL = "โฟล์แรก — เลือกบริษัท"
FLOW_1_END_LABEL = "โฟล์สุดท้าย — เปลี่ยนบริษัท"
FLOW_2_LABEL = "โฟล์ 2 — สมุดรายวันจ่าย (PV)"

FULL_SEQUENCE_NOTE = "บริษัทเดียว — เปิด PV (5→1→2) แล้วทำทุกแถวทุกชีต"

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
    PHASE_FLOW_1_START: f"{FLOW_1_LABEL} (ค้นหาในหน้าเลือกข้อมูล)",
    PHASE_FLOW_2_OPEN: f"{FLOW_2_LABEL} — เปิด (5→1→2)",
    PHASE_FLOW_2_NEW: f"{FLOW_2_LABEL} — สร้างรายการ (F2)",
    PHASE_FLOW_2_HEADER: f"{FLOW_2_LABEL} — กรอกหัวเรื่อง",
    PHASE_FLOW_2_SERVICE: f"{FLOW_2_LABEL} — 5330-05",
    PHASE_FLOW_2_VAT: f"{FLOW_2_LABEL} — 1154-00",
    PHASE_FLOW_2_TAX_DIALOG: f"{FLOW_2_LABEL} — Dialog ใบกำกับ",
    PHASE_FLOW_2_WT_DIALOG: f"{FLOW_2_LABEL} — Dialog WT (ยกเลิก)",
    PHASE_FLOW_2_CASH: f"{FLOW_2_LABEL} — 1111-00",
    PHASE_FLOW_2_SAVE: f"{FLOW_2_LABEL} — บันทึก (F10)",
    PHASE_FLOW_1_END: f"{FLOW_1_END_LABEL} (กด {MENU_OTHERS})",
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


def build_flow1_detail(*, press_menu_others: bool) -> tuple[FlowStepSpec, ...]:
    """press_menu_others=False → โฟล์แรก (อยู่หน้าเลือกข้อมูลแล้ว)
    press_menu_others=True  → โฟล์สุดท้าย (กด 8 ก่อน)
    """
    steps: list[FlowStepSpec] = []
    n = 1

    if press_menu_others:
        steps.append(
            FlowStepSpec(
                n,
                "key",
                "กดเมนู 8. อื่นๆ",
                MENU_OTHERS,
                "จากหน้าเมนูหลัก — เฉพาะโฟล์สุดท้าย",
            )
        )
        n += 1

    steps.extend(
        [
            FlowStepSpec(
                n,
                "wait",
                "รอ Dialog เลือกข้อมูล",
                note="ตารางรายการชื่อข้อมูล/บริษัท (หน้าแรกของโฟล์เลือกบริษัท)",
            ),
            FlowStepSpec(
                n + 1,
                "click",
                "คลิก ค้นหา",
                note="ปุ่ม ค้นหา ด้านล่าง dialog — btn_search.png",
            ),
            FlowStepSpec(
                n + 2,
                "wait",
                "รอช่องค้นหาเปิด",
                note="dialog ชื่อข้อมูล / ช่องพิมพ์ชื่อบริษัท",
            ),
            FlowStepSpec(
                n + 3,
                "type",
                "พิมพ์ชื่อบริษัทเต็ม",
                note="ชื่อเต็มตรงกับใน Express (จากช่อง UI)",
            ),
            FlowStepSpec(n + 4, "enter", "Enter ครั้งที่ 1", note="เลือกรายการที่ค้นหาเจอ"),
            FlowStepSpec(
                n + 5,
                "enter",
                "Enter ครั้งที่ 2",
                note="ยืนยัน — dialog วันที่ทำการ เด้งขึ้นเลย (ไม่ต้องกด ตกลง dialog เลือกข้อมูล)",
            ),
            FlowStepSpec(
                n + 6,
                "click",
                "คลิก ตกลง (วันที่ทำการ)",
                note="btn_ok.png หรือ Enter",
            ),
            FlowStepSpec(n + 7, "wait", "กลับหน้าเมนูหลัก", note="พร้อมเปิด PV (5→1→2)"),
        ]
    )
    return tuple(steps)


FLOW_1_START_DETAIL = build_flow1_detail(press_menu_others=False)
FLOW_1_END_DETAIL = build_flow1_detail(press_menu_others=True)

FLOW_1_STEPS_START: tuple[str, ...] = tuple(
    f"{s.step_no}. {s.label}" + (f" → {s.value}" if s.value else "") for s in FLOW_1_START_DETAIL
)
FLOW_1_STEPS_END: tuple[str, ...] = tuple(
    f"{s.step_no}. {s.label}" + (f" → {s.value}" if s.value else "") for s in FLOW_1_END_DETAIL
)
