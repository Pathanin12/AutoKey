from __future__ import annotations

import threading
import time
from typing import Callable

from constants.flow_model import (
    FLOW_1_END_LABEL,
    FLOW_1_LABEL,
    STEP_REGION_FLOW_1_END,
    STEP_REGION_FLOW_1_START,
)
from constants.step_regions import get_step_region
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_SERVICE,
    ACCOUNT_VAT,
    MENU_ACCOUNT,
    MENU_DAILY_ENTRY,
    MENU_PAYMENT_JOURNAL,
)
from models.ka_tam_row import KaTamRow
from models.run_config import RunConfig
from models.screen_region import ScreenRegion
from services.image_service import ImageService, MatchResult
from services.company_switch_service import CompanySwitchSettings, select_company
from services.tax_reference_service import resolve_tax_payer_id


class KaTamWorkflow:
    TEMPLATE_NEW = "pv_new.png"
    TEMPLATE_SAVE = "pv_save.png"
    TEMPLATE_OK = "btn_ok.png"
    TEMPLATE_CANCEL = "btn_cancel.png"
    TEMPLATE_SEARCH = "btn_search.png"
    TEMPLATE_WT_DIALOG = "wt_dialog.png"
    TEMPLATE_TAX_DIALOG = "tax_invoice_dialog.png"

    STEP_OPEN_MENU = 1
    STEP_NEW_VOUCHER = 2
    STEP_HEADER = 3
    STEP_SERVICE = 4
    STEP_VAT = 5
    STEP_TAX_INVOICE = 6
    STEP_WT = 7
    STEP_CASH = 8
    STEP_SAVE = 9

    def __init__(
        self,
        image_service: ImageService,
        stop_event: threading.Event,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        on_step: Callable[[int, str, str], None] | None = None,
        on_highlight: Callable[[ScreenRegion], None] | None = None,
        dry_run: bool = False,
        company_switch_settings: CompanySwitchSettings | None = None,
    ) -> None:
        self.image = image_service
        self.stop_event = stop_event
        self.on_status = on_status
        self.on_progress = on_progress
        self.on_step = on_step
        self.on_highlight = on_highlight
        self.dry_run = dry_run
        self.company_switch_settings = company_switch_settings

    def run(
        self,
        config: RunConfig,
        rows: list[KaTamRow],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        report_progress = progress_callback or self.on_progress
        self._step(self.STEP_OPEN_MENU, "เปิดเมนูสมุดรายวันจ่าย", "5 > 1 > 2")
        self._open_payment_journal()

        total = len(rows)
        for index, row in enumerate(rows, start=1):
            self._check_stop()
            report_progress(index, total)
            row_detail = f"แถว {row.row_number}: {row.legal_name}"
            self._status(row_detail)

            self._step(self.STEP_NEW_VOUCHER, "สร้างรายการใหม่", row_detail)
            self._create_voucher(config, row)

            self._step(self.STEP_HEADER, "กรอกหัวเรื่อง", row_detail)
            self._fill_header(config, row)

            self._step(
                self.STEP_SERVICE,
                "กรอกบัญชีค่าบริการ",
                f"{ACCOUNT_SERVICE} เดบิต {self._format_amount(row.service_amount)}",
            )
            self._fill_service_line(row)

            if row.has_vat:
                self._step(
                    self.STEP_VAT,
                    "กรอกบัญชีภาษีซื้อ",
                    f"{ACCOUNT_VAT} เดบิต {self._format_amount(row.vat_amount)}",
                )
                self._fill_vat_line(config, row)

            self._step(
                self.STEP_CASH,
                "กรอกบัญชีเงินสด",
                f"{ACCOUNT_CASH} เครดิต {self._format_amount(row.credit_amount - row.wt_amount if row.has_wt else row.credit_amount)}",
            )
            self._fill_cash_line(row)

            self._step(self.STEP_SAVE, "บันทึกรายการ", row_detail)
            self._save_voucher()
            self._status(f"บันทึกแล้ว: {row.legal_name}")

    def _step(self, step_index: int, step_label: str, detail: str = "") -> None:
        self._status(step_label if not detail else f"{step_label} — {detail}")
        if self.on_step:
            self.on_step(step_index, step_label, detail)
        self._highlight_step(step_index, step_label, detail)

    def _highlight_step(self, step_index: int, step_label: str, detail: str = "") -> None:
        if not self.on_highlight:
            return
        region = get_step_region(step_index)
        if region is None:
            return
        label = step_label if not detail else f"{step_label} — {detail}"
        self.on_highlight(
            ScreenRegion(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                label=label,
            )
        )

    def _highlight_match(self, match: MatchResult | None, label: str) -> None:
        if not self.on_highlight or match is None:
            return
        self.on_highlight(ScreenRegion.from_match(match.x, match.y, match.width, match.height, label))

    def _simulate(self, seconds: float = 0.35) -> None:
        if self.dry_run:
            time.sleep(seconds)

    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise InterruptedError("หยุดโดยผู้ใช้")

    def _status(self, message: str) -> None:
        self.on_status(message)

    def _open_payment_journal(self) -> None:
        if self.dry_run:
            self._simulate(0.5)
            return
        self.image.press(MENU_ACCOUNT)
        self.image.wait(0.8)
        self.image.press(MENU_DAILY_ENTRY)
        self.image.wait(0.8)
        self.image.press(MENU_PAYMENT_JOURNAL)
        self.image.wait(1.5)

    def select_company_flow(self, company_name: str, *, is_final: bool = False) -> None:
        label = FLOW_1_END_LABEL if is_final else FLOW_1_LABEL
        step_index = STEP_REGION_FLOW_1_END if is_final else STEP_REGION_FLOW_1_START
        self._step(step_index, label, company_name)
        self._status(f"{label}: {company_name}")
        if self.dry_run:
            self._simulate(0.8)
            return
        if self.company_switch_settings is None:
            return
        select_company(
            self.image,
            company_name,
            self.company_switch_settings,
            press_menu_others=is_final,
        )

    def switch_company_after_flow(self, company_name: str) -> None:
        self.select_company_flow(company_name, is_final=True)

    def _create_voucher(self, config: RunConfig, row: KaTamRow) -> None:
        if self.dry_run:
            self._simulate()
            return
        match = self.image.locate(self.TEMPLATE_NEW)
        if match:
            self._highlight_match(match, "ปุ่ม New")
            self.image.click_center(match)
            return
        self.image.press("f2")
        self.image.wait(0.8)
        if not config.use_work_date and config.pv_date.strip():
            self.image.type_text(config.pv_date.strip(), clear_first=True)

    def _fill_header(self, config: RunConfig, row: KaTamRow) -> None:
        if self.dry_run:
            self._simulate()
            return
        self.image.press("tab", presses=2)
        if not config.use_work_date and config.pv_date.strip():
            self.image.type_text(config.pv_date.strip(), clear_first=True)
        self.image.press("tab", presses=2)
        self.image.type_thai(config.description.strip(), clear_first=True)

    def _fill_service_line(self, row: KaTamRow) -> None:
        self._enter_grid_row(
            account_code=ACCOUNT_SERVICE,
            vendor_name=row.legal_name,
            debit=row.service_amount,
        )

    def _fill_vat_line(self, config: RunConfig, row: KaTamRow) -> None:
        self._enter_grid_row(
            account_code=ACCOUNT_VAT,
            vendor_name=row.legal_name,
            debit=row.vat_amount,
        )
        self._fill_tax_invoice_dialog(config, row)

    def _fill_cash_line(self, row: KaTamRow) -> None:
        credit_amount = row.credit_amount
        if row.has_wt:
            credit_amount = round(row.credit_amount - row.wt_amount, 2)
        self._enter_grid_row(
            account_code=ACCOUNT_CASH,
            vendor_name=row.legal_name,
            credit=credit_amount,
        )

    def _enter_grid_row(
        self,
        account_code: str,
        vendor_name: str,
        debit: float | None = None,
        credit: float | None = None,
    ) -> None:
        if self.dry_run:
            self._simulate()
            return
        self.image.type_text(account_code, clear_first=True)
        self.image.press("tab")
        self.image.press("tab")
        self.image.type_thai(vendor_name, clear_first=True)
        self.image.press("tab")
        if debit is not None and debit > 0:
            self.image.type_text(self._format_amount(debit), clear_first=True)
            self.image.press("tab")
        elif credit is not None and credit > 0:
            self.image.press("tab")
            self.image.type_text(self._format_amount(credit), clear_first=True)
        self.image.press("enter")

    def _fill_tax_invoice_dialog(self, config: RunConfig, row: KaTamRow) -> None:
        tax_payer_id = resolve_tax_payer_id(row.tax_id, config.tax_payer_id)
        self._step(
            self.STEP_TAX_INVOICE,
            "กรอกใบกำกับภาษีซื้อ",
            f"เลขที่ {row.tax_invoice_number} / เลขผู้เสียภาษี {tax_payer_id or '-'}",
        )
        if self.dry_run:
            self._simulate(0.5)
            return
        try:
            match = self._wait_locate(self.TEMPLATE_TAX_DIALOG, timeout=3)
        except TimeoutError:
            return
        self._highlight_match(match, "Dialog ใบกำกับภาษีซื้อ")
        self.image.click_center(match)

        invoice_number = row.tax_invoice_number
        self.image.type_text(invoice_number, clear_first=True)
        self.image.press("enter")
        if tax_payer_id:
            self.image.type_text(tax_payer_id, clear_first=True)
        self._click_ok()
        self._dismiss_auto_wt_dialog()

    def _dismiss_auto_wt_dialog(self) -> None:
        self._step(
            self.STEP_WT,
            "ปิด Dialog ภาษีหัก ณ ที่จ่าย",
            "กด ยกเลิก — เด้งอัตโนมัติหลัง ตกลง ใบกำกับ",
        )
        if self.dry_run:
            self._simulate(0.3)
            return
        try:
            match = self._wait_locate(self.TEMPLATE_WT_DIALOG, timeout=5)
            self._highlight_match(match, "Dialog ภาษีหัก ณ ที่จ่าย")
        except TimeoutError:
            return
        self._click_cancel()

    def _save_voucher(self) -> None:
        if self.dry_run:
            self._simulate()
            return
        match = self.image.locate(self.TEMPLATE_SAVE)
        if match:
            self._highlight_match(match, "ปุ่ม Save")
            self.image.click_center(match)
            self.image.wait(1.0)
            return
        self.image.press("f10")
        self.image.wait(1.0)

    def _wait_locate(self, template_name: str, timeout: float = 10.0) -> MatchResult:
        deadline = time.time() + timeout
        while time.time() < deadline:
            self._check_stop()
            match = self.image.locate(template_name)
            if match:
                return match
            time.sleep(0.3)
        raise TimeoutError(f"ไม่พบภาพ template: {template_name}")

    def _click_ok(self) -> None:
        if self.dry_run:
            self._simulate(0.2)
            return
        match = self.image.locate(self.TEMPLATE_OK)
        if match:
            self._highlight_match(match, "ปุ่ม ตกลง")
            self.image.click_center(match)
            return
        self.image.press("enter")

    def _click_cancel(self) -> None:
        if self.dry_run:
            self._simulate(0.2)
            return
        match = self.image.locate(self.TEMPLATE_CANCEL)
        if match:
            self._highlight_match(match, "ปุ่ม ยกเลิก")
            self.image.click_center(match)
            return
        self.image.press("escape")

    @staticmethod
    def _format_amount(value: float) -> str:
        return f"{value:,.2f}"
