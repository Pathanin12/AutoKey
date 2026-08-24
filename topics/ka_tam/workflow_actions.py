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
    MENU_OTHERS_CHANGE_COMPANY,
    MENU_PAYMENT_JOURNAL,
    VENDOR_LOOKUP_KEY,
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
    "company_name": "โชคธนา (2004)",
}

def build_workflow_actions() -> list[WorkflowAction]:
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

    def add_flow1_start(phase: int) -> None:
        add(
            phase,
            "tab",
            "1. Tab → ปุ่ม ค้นหา",
            note="Tab ×2 (lookup_search.button_tabs)",
            image_key="company_select",
        )
        add(
            phase,
            "enter",
            "2. Enter → เปิดช่องค้นหา",
            note="แทนคลิกปุ่ม ค้นหา",
            image_key="company_select",
        )
        add(
            phase,
            "type",
            "3. พิมพ์ชื่อบริษัท",
            sample["company_name"],
            note="จากฟอร์ม AutoKey",
            image_key="company_select",
        )
        add(
            phase,
            "enter",
            "4. Enter ครั้งที่ 1",
            note="เลือกรายการ",
            image_key="company_select",
        )
        add(
            phase,
            "enter",
            "5. Enter ครั้งที่ 2",
            note="ยืนยัน → เข้าเมนูหลัก",
            image_key="company_select",
        )

    def add_pv_row() -> None:
        add(2, "fkey", "1. กด F2 สร้างรายการใหม่", "F2", image_key="pv_main")
        add(2, "wait", "2. รอฟอร์มเปิด", note="0.8 วินาที", image_key="pv_main")
        add(2, "type", "3. พิมพ์วันที่ใบสำคัญ (ตอนสร้าง)", sample["pv_date"], image_key="pv_main")

        add(3, "tab", "1. Tab → ช่องวันที่", note="ครั้งที่ 1", image_key="pv_header")
        add(3, "tab", "2. Tab → ช่องวันที่", note="ครั้งที่ 2", image_key="pv_header")
        add(3, "type", "3. พิมพ์วันที่ใบสำคัญ", sample["pv_date"], image_key="pv_header")
        add(3, "tab", "4. Tab → ช่องรายละเอียด", note="ครั้งที่ 1", image_key="pv_header")
        add(3, "tab", "5. Tab → ช่องรายละเอียด", note="ครั้งที่ 2", image_key="pv_header")
        add(3, "type", "6. พิมพ์รายละเอียด", sample["description"], image_key="pv_header")

        def grid_row_numbered(
            phase: int,
            start: int,
            account_code: str,
            account_label: str,
            amount_key: str,
            amount_note: str,
            *,
            is_credit: bool = False,
            image_key: str = "pv_grid",
        ) -> None:
            n = start
            add(phase, "type", f"{n}. พิมพ์รหัสบัญชี — {account_label}", account_code, image_key=image_key)
            add(phase, "tab", f"{n + 1}. Tab → sub-account", image_key=image_key)
            add(phase, "tab", f"{n + 2}. Tab → ชื่อผู้ขาย/ผู้รับ", image_key=image_key)
            add(
                phase,
                "fkey",
                f"{n + 3}. กด {VENDOR_LOOKUP_KEY.upper()} เปิด dialog เลือกข้อมูล",
                VENDOR_LOOKUP_KEY.upper(),
                image_key="company_select",
            )
            add(
                phase,
                "tab",
                f"{n + 4}. Tab → ปุ่ม ค้นหา",
                note="Tab ×2 (lookup_search.button_tabs)",
                image_key="company_select",
            )
            add(
                phase,
                "enter",
                f"{n + 5}. Enter → เปิดช่องค้นหา",
                note="แทนคลิกปุ่ม ค้นหา",
                image_key="company_select",
            )
            add(
                phase,
                "type",
                f"{n + 6}. พิมพ์ชื่อนิติบุคคล",
                sample["legal_name"],
                image_key="company_select",
            )
            add(
                phase,
                "enter",
                f"{n + 7}. Enter → เลือกรายการ",
                image_key="company_select",
            )
            add(phase, "tab", f"{n + 8}. Tab → ช่องเดบิต", image_key=image_key)
            if is_credit:
                add(phase, "tab", f"{n + 9}. Tab → ข้ามเดบิต ไปเครดิต", image_key=image_key)
                add(phase, "type", f"{n + 10}. {amount_note}", sample[amount_key], image_key=image_key)
                add(phase, "enter", f"{n + 11}. Enter → ยืนยันแถว", image_key=image_key)
            else:
                add(phase, "type", f"{n + 9}. {amount_note}", sample[amount_key], image_key=image_key)
                add(phase, "tab", f"{n + 10}. Tab → ช่องถัดไป", image_key=image_key)
                add(phase, "enter", f"{n + 11}. Enter → ยืนยันแถว", image_key=image_key)

        grid_row_numbered(4, 1, ACCOUNT_SERVICE, "ค่าบริการ 5330-05", "service_amount", "พิมพ์ยอดเดบิต srv")
        grid_row_numbered(5, 1, ACCOUNT_VAT, "ภาษีซื้อ 1154-00", "vat_amount", "พิมพ์ยอดเดบิต vat")

        add(6, "wait", "1. รอ Dialog ใบกำกับภาษีซื้อ", note="popup หลัง 1154-00", image_key="tax_dialog")
        add(
            6,
            "type",
            "2. พิมพ์ เลขที่ใบกำกับภาษี",
            sample["invoice_number"],
            note="NRG+ปี+เดือน+ลำดับ",
            image_key="tax_dialog",
        )
        add(
            6,
            "enter",
            "3. Enter → Express กรอกช่องอื่นอัตโนมัติ",
            note="cursor ไปเลขผู้เสียภาษี",
            image_key="tax_dialog",
        )
        add(
            6,
            "type",
            "4. พิมพ์ เลขประจำตัวผู้เสียภาษี",
            sample["tax_payer_id"],
            image_key="tax_dialog",
        )
        add(6, "enter", "5. Enter → ตกลง ใบกำกับ", note="Enter", image_key="tax_dialog")

        add(
            7,
            "wait",
            "1. รอ Dialog ภาษีหัก ณ ที่จ่าย",
            note="เด้งอัตโนมัติหลัง ตกลง ใบกำกับ",
            image_key="wt_dialog",
        )
        add(
            7,
            "fkey",
            "2. กด Esc ยกเลิก",
            "Esc",
            note="ไม่กรอก WT",
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

        add(9, "fkey", "1. กด F10 บันทึก", "F10", image_key="pv_grid")
        add(
            9,
            "wait",
            "2. รอ Dialog ป้อนรายละเอียดรายการภาษีซื้อ",
            note="Express กรอกวันที่/ยอด/ชื่อให้แล้ว — ไม่พิมพ์เลขที่",
            image_key="tax_dialog",
        )
        add(
            9,
            "tab",
            "3. Tab → ช่องเลขประจำตัวผู้เสียภาษี",
            note="Tab ×6 จากช่องเลขที่ (ว่าง)",
            image_key="tax_dialog",
        )
        add(
            9,
            "type",
            "4. พิมพ์ เลขประจำตัวผู้เสียภาษี",
            sample["tax_payer_id"],
            image_key="tax_dialog",
        )
        add(
            9,
            "enter",
            "5. Enter → ตกลง",
            note="จบ 1 แถว — แล้วค่อย F2 แถวถัดไป",
            image_key="tax_dialog",
        )
        add(9, "wait", "6. รอกลับหน้า PV", note="0.8 วินาที", image_key="pv_grid")

    # ══════════════════════════════════════════
    # โฟล์ 1 — เลือกบริษัท (AutoKey ทำให้)
    # ══════════════════════════════════════════
    add_section(
        "▶ โฟล์ 1 — เลือกบริษัท",
        note="กดเริ่มแล้วทำทันที — ชื่อบริษัทจากฟอร์ม",
    )
    add_flow1_start(0)

    # ══════════════════════════════════════════
    # เปิด PV (ครั้งเดียวต่อชีต)
    # ══════════════════════════════════════════
    add_section("▶ เปิดสมุดรายวันจ่าย", note="หลังโฟล์ 1 — อยู่หน้าเมนูหลัก")
    add(1, "key", "1. กด 5. บัญชี", MENU_ACCOUNT, image_key="menu_open_pv")
    add(1, "wait", "2. รอเมนูย่อย", note="0.8 วินาที", image_key="menu_open_pv")
    add(1, "key", "3. กด 1. ลงประจำวัน", MENU_DAILY_ENTRY, image_key="menu_open_pv")
    add(1, "wait", "4. รอเมนูย่อย", note="0.8 วินาที", image_key="menu_open_pv")
    add(1, "key", "5. กด 2. สมุดรายวันจ่าย", MENU_PAYMENT_JOURNAL, image_key="menu_open_pv")
    add(1, "wait", "6. รอหน้า PV เปิด", note="1.5 วินาที", image_key="menu_open_pv")

    # ══════════════════════════════════════════
    # โฟล์ 2 — 1 แถว Excel (ตัวอย่างแถวที่ 1)
    # ══════════════════════════════════════════
    add_section("▶ โฟล์ 2 — ทำแถว Excel ที่ 1", note="Phase 2–9 ต่อ 1 รายการ")
    add_pv_row()

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

    add(
        10,
        "section",
        "✓ จบ AutoKey",
        note="ครบทุกแถว — ยังอยู่ DB เดิม (8→8 ทำเองเมื่อจะเปลี่ยนฐานข้อมูล)",
        region_step=0,
        image_key="pv_grid",
    )

    return actions
