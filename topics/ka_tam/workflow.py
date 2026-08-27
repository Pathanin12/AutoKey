from __future__ import annotations

import threading
from typing import Callable

from constants.flow_model import FLOW_1_END_LABEL, FLOW_1_LABEL
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_SERVICE,
    ACCOUNT_VAT,
    MENU_PAYMENT_JOURNAL_PATH,
    VENDOR_LOOKUP_KEY,
)
from models.ka_tam_row import KaTamRow
from models.run_config import RunConfig
from services.image_service import ImageService
from services.company_switch_service import (
    CompanySwitchSettings,
    open_change_company_menu,
    select_company_on_dialog,
)
from models.run_failure import RunFailureError
from services.lookup_search_service import (
    LookupSearchSettings,
    LookupSelectionMismatchError,
    search_and_select,
)
from services.template_click_service import TemplateClickService
from services.menu_navigation_service import open_payment_journal_menu
from services.tax_reference_service import resolve_tax_payer_id


class KaTamWorkflow:
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
        company_switch_settings: CompanySwitchSettings | None = None,
        lookup_search_settings: LookupSearchSettings | None = None,
        template_click_service: TemplateClickService | None = None,
        verbose_log: bool = False,
    ) -> None:
        self.image = image_service
        self.stop_event = stop_event
        self.on_status = on_status
        self.on_progress = on_progress
        self.on_step = on_step
        self.verbose_log = verbose_log
        self.company_switch_settings = company_switch_settings
        self.lookup_search_settings = lookup_search_settings or LookupSearchSettings()
        self.template_click = template_click_service

    def run(
        self,
        config: RunConfig,
        rows: list[KaTamRow],
        progress_callback: Callable[[int, int], None] | None = None,
        *,
        open_payment_journal: bool = False,
    ) -> None:
        report_progress = progress_callback or self.on_progress
        if open_payment_journal:
            self._step(self.STEP_OPEN_MENU, "เปิดเมนูสมุดรายวันจ่าย", MENU_PAYMENT_JOURNAL_PATH)
            self._open_payment_journal()

        total = len(rows)
        completed_count = 0
        for index, row in enumerate(rows, start=1):
            self._check_stop()
            report_progress(index, total)
            row_detail = f"แถว {row.row_number}: {row.legal_name}"
            self._status(f"[{index}/{total}] {row_detail}")

            try:
                self._check_stop()
                self._step(self.STEP_NEW_VOUCHER, "สร้างรายการใหม่", row_detail)
                self._create_voucher(config, row)

                self._check_stop()
                self._step(self.STEP_HEADER, "กรอกหัวเรื่อง", row_detail)
                self._fill_header(config, row)

                self._check_stop()
                self._step(
                    self.STEP_SERVICE,
                    "กรอกบัญชีค่าบริการ",
                    f"{ACCOUNT_SERVICE} เดบิต {self._format_amount(row.service_amount)}",
                )
                self._fill_service_line(row)

                if row.has_vat:
                    self._check_stop()
                    self._step(
                        self.STEP_VAT,
                        "กรอกบัญชีภาษีซื้อ",
                        f"{ACCOUNT_VAT} เดบิต {self._format_amount(row.vat_amount)}",
                    )
                    self._fill_vat_line(config, row)

                self._check_stop()
                self._step(
                    self.STEP_CASH,
                    "กรอกบัญชีเงินสด",
                    f"{ACCOUNT_CASH} เครดิต {self._format_amount(row.credit_amount - row.wt_amount if row.has_wt else row.credit_amount)}",
                )
                self._fill_cash_line(row)

                self._check_stop()
                self._step(self.STEP_SAVE, "บันทึกรายการ", row_detail)
                self._save_voucher(config, row)
            except LookupSelectionMismatchError as exc:
                raise RunFailureError(
                    message=str(exc),
                    completed_count=completed_count,
                    failed_no=row.sequence,
                    failed_name=row.legal_name,
                    sheet_name=row.sheet_name,
                ) from exc

            completed_count += 1
            self._status(f"✓ [{index}/{total}] {row.legal_name}")

    def _step(self, step_index: int, step_label: str, detail: str = "") -> None:
        if not self.verbose_log:
            return
        message = step_label if not detail else f"{step_label} — {detail}"
        self._status(message)
        if self.on_step:
            self.on_step(step_index, step_label, detail)

    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise InterruptedError("หยุดโดยผู้ใช้")

    def _status(self, message: str) -> None:
        self.on_status(message)

    def _open_payment_journal(self) -> None:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-2")

        open_payment_journal_menu(
            self.image,
            self.template_click,
            on_status=self.on_status,
            template_retries=self.lookup_search_settings.template_retries,
            template_retry_delay=self.lookup_search_settings.template_retry_delay,
        )

    def open_payment_journal_after_lookup(self, query: str) -> None:
        name = query.strip()
        if not name:
            raise RuntimeError("ไม่พบชื่อสำหรับค้นหาใน dialog เลือกข้อมูล")

        self._status(f"ค้นหาใน dialog: {name}")
        search_and_select(
            self.image,
            self.lookup_search_settings,
            name,
            template_click=self.template_click,
            on_status=self.on_status,
        )
        self.open_payment_journal_only()

    def open_payment_journal_only(self) -> None:
        self._step(self.STEP_OPEN_MENU, "เปิดเมนูสมุดรายวันจ่าย", MENU_PAYMENT_JOURNAL_PATH)
        self._open_payment_journal()

    def select_company_flow(self, company_name: str) -> None:
        name = company_name.strip()
        if not name:
            return
        self._step(1, FLOW_1_LABEL, f"จับภาพ ค้นหา → {name}")
        self._status(f"{FLOW_1_LABEL}: {name}")
        if self.company_switch_settings is None:
            return
        select_company_on_dialog(
            self.image,
            name,
            self.company_switch_settings,
            template_click=self.template_click,
        )

    def return_to_main_menu(self) -> None:
        if self.company_switch_settings is None:
            return
        count = max(0, self.company_switch_settings.exit_pv_esc_count)
        for _ in range(count):
            self.image.press("esc")
            self.image.wait(0.5)

    def open_change_company_flow(self) -> None:
        self._step(10, FLOW_1_END_LABEL, "8 → 8 เปลี่ยนบริษัท")
        self._status(f"{FLOW_1_END_LABEL}: กด 8 → 8")
        if self.company_switch_settings is None:
            return
        self.return_to_main_menu()
        open_change_company_menu(self.image, self.company_switch_settings)

    def _create_voucher(self, config: RunConfig, row: KaTamRow) -> None:
        self.image.press("f2")
        self.image.wait(0.15)
        if config.pv_date.strip():
            self.image.type_text(config.pv_date.strip(), clear_first=True)

    def _fill_header(self, config: RunConfig, row: KaTamRow) -> None:
        self.image.press("tab", presses=2)
        if config.pv_date.strip():
            self.image.type_text(config.pv_date.strip(), clear_first=True)
        if config.description.strip():
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
        self.image.type_text(account_code, clear_first=False)
        self.image.press("tab")
        self.image.press("tab")
        self.image.press(VENDOR_LOOKUP_KEY)
        self.image.wait(0.1)
        search_and_select(
            self.image,
            self.lookup_search_settings,
            vendor_name,
            confirm_enter_count=1,
            template_click=self.template_click,
            on_status=self.on_status,
        )
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
        self.image.wait(0.8)
        self.image.type_text(row.tax_invoice_number, clear_first=True)
        self.image.press("enter")
        if tax_payer_id:
            self.image.type_text(tax_payer_id, clear_first=True)
        self.image.press("enter")
        self._dismiss_auto_wt_dialog()

    def _dismiss_auto_wt_dialog(self) -> None:
        self._step(
            self.STEP_WT,
            "ปิด Dialog ภาษีหัก ณ ที่จ่าย",
            "กด Esc — เด้งอัตโนมัติหลัง ตกลง ใบกำกับ",
        )
        self.image.wait(0.5)
        self.image.press("esc")

    def _fill_input_tax_summary_after_save(self, config: RunConfig, row: KaTamRow) -> None:
        """หลัง F10 — dialog ป้อนรายละเอียดรายการภาษีซื้อ (Express กรอกยอด/ชื่อให้แล้ว)"""
        tax_payer_id = resolve_tax_payer_id(row.tax_id, config.tax_payer_id)
        self._step(
            self.STEP_SAVE,
            "ยืนยันภาษีซื้อหลัง F10",
            f"เลขผู้เสียภาษี {tax_payer_id or '-'}",
        )
        self.image.wait(1.0)
        self.image.press("tab", presses=6)
        if tax_payer_id:
            self.image.type_text(tax_payer_id, clear_first=True)
        self.image.press("enter")
        self.image.wait(0.8)

    def _save_voucher(self, config: RunConfig, row: KaTamRow) -> None:
        self.image.press("f10")
        self.image.wait(1.0)
        if row.has_vat:
            self._fill_input_tax_summary_after_save(config, row)

    @staticmethod
    def _format_amount(value: float) -> str:
        return f"{value:,.2f}"
