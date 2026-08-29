from __future__ import annotations

import threading
from typing import Callable

from constants.flow_model import FLOW_1_END_LABEL, FLOW_1_LABEL
from constants.date_utils import format_express_pv_date
from constants.routes import (
    ACCOUNT_SERVICE,
    ACCOUNT_VAT,
    ACCOUNT_WT,
    MENU_PAYMENT_JOURNAL_PATH,
    PV_NEW_FILE_KEYS,
)
from models.ka_tam_row import KaTamRow
from models.run_config import RunConfig
from models.window_focus_settings import WindowFocusSettings
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
    STEP_FINISH = 8

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
        express_focus_settings: WindowFocusSettings | None = None,
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
        self.express_focus_settings = express_focus_settings or WindowFocusSettings()

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
                if index > 1:
                    self._lookup_and_open_pv(row)

                self._check_stop()
                self._step(self.STEP_NEW_VOUCHER, "สร้างรายการใหม่", row_detail)
                self._create_voucher(config)

                self._check_stop()
                self._fill_pv_lines(config, row, prepare_next=index < total)
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
        self.image.wait(0.8)

    def open_payment_journal_after_lookup(self, row: KaTamRow) -> None:
        self._search_vendor(row, "ค้นหาใน dialog")
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

    def _create_voucher(self, config: RunConfig) -> None:
        """Alt+A เปิดไฟล์ใหม่ → Enter → วันที่ → Enter → รายละเอียด → Enter"""
        from services.window_focus_service import focus_express_window

        focus_express_window(self.express_focus_settings, on_status=self.on_status)
        self._status("กด Alt+A สร้างรายการใหม่")
        self.image.wait(0.5)
        self.image.press(*PV_NEW_FILE_KEYS)
        self.image.wait(0.6)
        self.image.press("enter")
        self.image.wait(0.4)

        pv_date = format_express_pv_date(config.pv_date)
        if pv_date:
            self.image.type_keys(pv_date, clear_first=True)
            self.image.wait(0.2)
        self.image.press("enter")
        self.image.wait(0.15)

        description = config.description.strip()
        if description:
            self.image.type_thai(description, clear_first=True)
        self.image.press("enter")
        self.image.wait(0.15)

    def _lookup_and_open_pv(self, row: KaTamRow) -> None:
        self._search_vendor(row, "ค้นหาบริษัทถัดไป")
        self.open_payment_journal_only()

    def _search_vendor(self, row: KaTamRow, status_prefix: str) -> None:
        name = row.legal_name.strip()
        if not name:
            raise RuntimeError("ไม่พบชื่อสำหรับค้นหาใน dialog เลือกข้อมูล")

        self._status(f"{status_prefix}: {name}")
        search_and_select(
            self.image,
            self.lookup_search_settings,
            name,
            template_click=self.template_click,
            on_status=self.on_status,
            should_stop=self.stop_event.is_set,
        )

    def _fill_pv_lines(self, config: RunConfig, row: KaTamRow, *, prepare_next: bool) -> None:
        self._step(
            self.STEP_SERVICE,
            "กรอกบัญชีค่าบริการ",
            f"{ACCOUNT_SERVICE} → srv {self._format_amount(row.service_amount)}",
        )
        self.image.type_text(ACCOUNT_SERVICE, clear_first=False)
        self.image.press("enter", presses=2)
        self.image.type_text(self._format_amount(row.service_amount), clear_first=True)
        self.image.press("enter")

        self._step(
            self.STEP_VAT,
            "กรอกบัญชีภาษีซื้อ",
            f"{ACCOUNT_VAT} → vat {self._format_amount(row.vat_amount)}",
        )
        self.image.type_text(ACCOUNT_VAT, clear_first=False)
        self.image.press("enter", presses=2)
        self.image.type_text(self._format_amount(row.vat_amount), clear_first=True)
        self.image.press("enter")

        self._step(
            self.STEP_WT,
            "กรอกบัญชีภาษีหัก ณ ที่จ่าย",
            f"{ACCOUNT_WT} → wt {self._format_amount(row.wt_amount)}",
        )
        self.image.type_text(ACCOUNT_WT, clear_first=False)
        self.image.press("enter", presses=3)
        self.image.type_text(self._format_amount(row.wt_amount), clear_first=True)
        self.image.press("enter", presses=5)

        self._fill_tax_invoice_via_f2_f9(config, row)

        if prepare_next:
            self._step(self.STEP_FINISH, "กลับ dialog เลือกข้อมูล", "Shift+F11 → Tab → Enter")
            self.image.press("shift", "f11")
            self.image.wait(0.3)
            self.image.press("tab")
            self.image.press("enter")
            self.image.wait(0.4)

    def _fill_tax_invoice_via_f2_f9(self, config: RunConfig, row: KaTamRow) -> None:
        tax_payer_id = resolve_tax_payer_id(row.tax_id, config.tax_payer_id)
        invoice_number = row.tax_invoice_number
        self._step(
            self.STEP_TAX_INVOICE,
            "กรอกใบกำกับภาษีซื้อ",
            f"F2 → F9 → {invoice_number} / {tax_payer_id or '-'}",
        )
        self.image.press("f2")
        self.image.press("f9")
        self.image.wait(0.8)
        if invoice_number:
            self.image.type_text(invoice_number, clear_first=True)
        self.image.press("enter", presses=13)
        if tax_payer_id:
            self.image.type_text(tax_payer_id, clear_first=True)
        self.image.press("enter", presses=3)
        self.image.press("esc")
        self.image.wait(0.3)

    @staticmethod
    def _format_amount(value: float) -> str:
        return f"{value:,.2f}"
