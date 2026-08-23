from __future__ import annotations

from models.workflow_action import WorkflowAction
from constants.flow_model import FULL_SEQUENCE_NOTE, PHASE_TITLES
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_SERVICE,
    ACCOUNT_VAT,
    MENU_ACCOUNT,
    MENU_DAILY_ENTRY,
    MENU_OTHERS,
    MENU_PAYMENT_JOURNAL,
)

SAMPLE_VALUES: dict[str, str] = {
    "legal_name": "บจก. ไดมอนด์ เอ็นเนอจี้ กรุ๊ป",
    "description": "ค่าทำบัญชี NRG",
    "pv_date": "25/04/2569",
    "invoice_number": "NRG2026070001",
    "tax_payer_id": "0145560000743",
    "service_amount": "2,000.00",
    "vat_amount": "140.00",
    "cash_credit": "2,080.00",
    "wt_amount": "60.00",
    "company_name": "บจก.ที.เอ็ม.มาร์ท",
    "next_company_name": "ห้างหุ้นส่วนจำกัด โชคธนา (2004)",
}

def build_workflow_actions(use_work_date: bool = True) -> list[WorkflowAction]:
    """{FULL_SEQUENCE_NOTE} — ไม่ข้ามขั้น""".format(FULL_SEQUENCE_NOTE=FULL_SEQUENCE_NOTE)
    sample = SAMPLE_VALUES
    actions: list[WorkflowAction] = []
    counter = 1

    def add(
        phase: int,
        kind: str,
        label: str,
        value: str = "",
        note: str = "",
        region_step: int | None = None,
        image_key: str = "pv_main",
    ) -> None:
        nonlocal counter
        actions.append(
            WorkflowAction(
                index=counter,
                phase=phase,
                phase_title=PHASE_TITLES[phase],
                kind=kind,
                label=label,
                value=value,
                note=note,
                region_step=region_step if region_step is not None else min(phase, 9),
                image_key=image_key,
            )
        )
        counter += 1

    def add_section(title: str, note: str = "") -> None:
        nonlocal counter
        actions.append(
            WorkflowAction(
                index=counter,
                phase=0,
                phase_title=title,
                kind="section",
                label=title,
                value="",
                note=note,
                region_step=0,
                image_key="company_select",
            )
        )
        counter += 1

    def add_flow1_company_select(phase: int, company_key: str) -> None:
        from constants.flow_model import (
            FLOW_1_END_DETAIL,
            FLOW_1_START_DETAIL,
            PHASE_FLOW_1_END,
            PHASE_FLOW_1_START,
        )

        region = PHASE_FLOW_1_END if phase == PHASE_FLOW_1_END else PHASE_FLOW_1_START
        detail = FLOW_1_END_DETAIL if phase == PHASE_FLOW_1_END else FLOW_1_START_DETAIL
        company_full_name = sample[company_key]
        last_step_no = detail[-1].step_no

        for spec in detail:
            value = company_full_name if spec.kind == "type" else spec.value
            image_key = "menu" if spec.step_no == last_step_no else "company_select"
            add(
                phase,
                spec.kind,
                f"{spec.step_no}. {spec.label}",
                value,
                spec.note,
                image_key=image_key,
                region_step=region,
            )

    def add_pv_row(use_work: bool) -> None:
        add(2, "click", "1. คลิกปุ่ม New", note="ถ้าไม่เจอ template → F2")
        add(2, "fkey", "2. กด F2 สร้างรายการใหม่", "F2")
        add(2, "wait", "3. รอฟอร์มเปิด", note="0.8 วินาที")
        if not use_work:
            add(2, "type", "4. พิมพ์วันที่ใบสำคัญ (ตอนสร้าง)", sample["pv_date"])

        add(3, "tab", "1. Tab → ช่องวันที่", note="ครั้งที่ 1")
        add(3, "tab", "2. Tab → ช่องวันที่", note="ครั้งที่ 2")
        if not use_work:
            add(3, "type", "3. พิมพ์วันที่ใบสำคัญ", sample["pv_date"])
        else:
            add(3, "wait", "3. ใช้วันที่ทำการจาก Express", note="ไม่พิมพ์วันที่")
        add(3, "tab", "4. Tab → ช่องรายละเอียด", note="ครั้งที่ 1")
        add(3, "tab", "5. Tab → ช่องรายละเอียด", note="ครั้งที่ 2")
        add(3, "type", "6. พิมพ์รายละเอียด", sample["description"])

        def grid_row_numbered(
            phase: int,
            start: int,
            account_code: str,
            account_label: str,
            amount_key: str,
            amount_note: str,
            *,
            is_credit: bool = False,
        ) -> None:
            n = start
            add(phase, "type", f"{n}. พิมพ์รหัสบัญชี — {account_label}", account_code)
            add(phase, "tab", f"{n + 1}. Tab → sub-account")
            add(phase, "tab", f"{n + 2}. Tab → ชื่อผู้ขาย/ผู้รับ")
            add(phase, "type", f"{n + 3}. พิมพ์ชื่อนิติบุคคล", sample["legal_name"])
            add(phase, "tab", f"{n + 4}. Tab → ช่องเดบิต")
            if is_credit:
                add(phase, "tab", f"{n + 5}. Tab → ข้ามเดบิต ไปเครดิต")
                add(phase, "type", f"{n + 6}. {amount_note}", sample[amount_key])
                add(phase, "enter", f"{n + 7}. Enter → ยืนยันแถว")
            else:
                add(phase, "type", f"{n + 5}. {amount_note}", sample[amount_key])
                add(phase, "tab", f"{n + 6}. Tab → ช่องถัดไป")
                add(phase, "enter", f"{n + 7}. Enter → ยืนยันแถว")

        grid_row_numbered(4, 1, ACCOUNT_SERVICE, "ค่าบริการ 5330-05", "service_amount", "พิมพ์ยอดเดบิต srv")
        grid_row_numbered(5, 1, ACCOUNT_VAT, "ภาษีซื้อ 1154-00", "vat_amount", "พิมพ์ยอดเดบิต vat")

        add(6, "wait", "1. รอ Dialog ใบกำกับภาษีซื้อ", note="popup หลัง 1154-00", image_key="tax_dialog")
        add(6, "click", "2. คลิก Dialog โฟกัส", image_key="tax_dialog")
        add(
            6,
            "type",
            "3. พิมพ์ เลขที่ใบกำกับภาษี",
            sample["invoice_number"],
            note="NRG+ปี+เดือน+ลำดับ",
            image_key="tax_dialog",
        )
        add(
            6,
            "enter",
            "4. Enter → Express กรอกช่องอื่นอัตโนมัติ",
            note="cursor ไปเลขผู้เสียภาษี",
            image_key="tax_dialog",
        )
        add(
            6,
            "type",
            "5. พิมพ์ เลขประจำตัวผู้เสียภาษี",
            sample["tax_payer_id"],
            image_key="tax_dialog",
        )
        add(6, "click", "6. คลิก ตกลง", note="btn_ok.png หรือ Enter", image_key="tax_dialog")

        add(
            7,
            "wait",
            "1. รอ Dialog ภาษีหัก ณ ที่จ่าย",
            note="เด้งอัตโนมัติหลัง ตกลง ใบกำกับ",
            image_key="wt_dialog",
        )
        add(
            7,
            "click",
            "2. คลิก ยกเลิก",
            note="btn_cancel.png — ไม่กรอก WT",
            image_key="wt_dialog",
        )

        grid_row_numbered(
            8,
            1,
            ACCOUNT_CASH,
            "เงินสด 1111-00",
            "cash_credit",
            "พิมพ์ยอดเครดิต",
            is_credit=True,
        )

        add(9, "click", "1. คลิก Save", note="pv_save.png")
        add(9, "fkey", "2. กด F10 บันทึก", "F10")
        add(9, "wait", "3. รอบันทึกเสร็จ", note="1.0 วินาที")

    # ══════════════════════════════════════════
    # โฟล์แรก — เลือกบริษัท (FLOW_1 ตอนเริ่ม — AutoKey ทำให้ ไม่ใช่เลือกเอง)
    # ══════════════════════════════════════════
    add_section(
        "▶ โฟล์แรก — เลือกบริษัท (ค้นหาเลย)",
        note="เปิด Express อยู่หน้า Dialog เลือกข้อมูลแล้ว — ไม่กด 8",
    )
    add_flow1_company_select(0, "company_name")

    # ══════════════════════════════════════════
    # โฟล์ 2 — เปิด PV (ครั้งเดียวต่อชีต)
    # ══════════════════════════════════════════
    add_section("▶ โฟล์ 2 — เปิดสมุดรายวันจ่าย", note="หลังโฟล์แรก — อยู่หน้าเมนูหลักแล้ว")
    add(1, "key", "1. กด 5. บัญชี", MENU_ACCOUNT, image_key="menu")
    add(1, "wait", "2. รอเมนูย่อย", note="0.8 วินาที", image_key="menu")
    add(1, "key", "3. กด 1. ลงประจำวัน", MENU_DAILY_ENTRY, image_key="menu")
    add(1, "wait", "4. รอเมนูย่อย", note="0.8 วินาที", image_key="menu")
    add(1, "key", "5. กด 2. สมุดรายวันจ่าย", MENU_PAYMENT_JOURNAL, image_key="menu")
    add(1, "wait", "6. รอหน้า PV เปิด", note="1.5 วินาที", image_key="menu")

    # ══════════════════════════════════════════
    # โฟล์ 2 — 1 แถว Excel (ตัวอย่างแถวที่ 1)
    # ══════════════════════════════════════════
    add_section("▶ โฟล์ 2 — ทำแถว Excel ที่ 1", note="Phase 2–9 ต่อ 1 รายการ")
    add_pv_row(use_work_date)

    # ══════════════════════════════════════════
    # วนซ้ำแถวถัดไป
    # ══════════════════════════════════════════
    add(
        2,
        "section",
        "↻ วนซ้ำ Phase 2–9 สำหรับแถว Excel ที่ 2, 3, …",
        note="ทำซ้ำจนครบทุกแถวทุกชีต — ไม่ต้องกด 5→1→2 ใหม่",
        region_step=2,
    )

    # ══════════════════════════════════════════
    # โฟล์สุดท้าย — กด 8 เปลี่ยนบริษัท
    # ══════════════════════════════════════════
    add_section(
        "▶ โฟล์สุดท้าย — เปลี่ยนบริษัท (กด 8)",
        note="หลัง Save แถวสุดท้าย — ขั้นตอนเดียวกับโฟล์แรก",
    )
    add_flow1_company_select(10, "next_company_name")
    add(
        10,
        "section",
        "✓ จบ AutoKey",
        note="พร้อมทำบริษัท/ชุดข้อมูลถัดไป",
        region_step=0,
        image_key="company_select",
    )

    return actions
