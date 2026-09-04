from __future__ import annotations

import threading
from typing import Callable

from constants.date_utils import format_express_pv_date
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PP30_DECIMAL,
    ACCOUNT_PP30_VAT_PAYABLE,
    ACCOUNT_PP30_VAT_PURCHASE,
    ACCOUNT_PP30_VAT_SALE,
    MENU_GENERAL_JOURNAL_PATH,
    MENU_PAYMENT_JOURNAL_PATH,
    PP30_ACCOUNT_REPORT_CODES,
    PV_NEW_FILE_KEYS,
    UI_TEXT,
)
from models.pp30_form_config import Pp30FormConfig
from models.pp30_form_values import Pp30FormValues
from models.pp30_matched_job import Pp30MatchedJob
from services.account_report_capture_service import build_ledger_report_jobs, capture_account_reports
from services.company_switch_service import CompanySwitchSettings, open_change_company_menu
from services.image_service import ImageService
from services.lookup_search_service import LookupSearchSettings, search_and_select
from services.menu_navigation_service import open_general_journal_menu, open_payment_journal_menu
from services.template_click_service import TemplateClickService


class Pp30Workflow:
    def __init__(
        self,
        image_service: ImageService,
        stop_event: threading.Event,
        on_status: Callable[[str], None],
        on_progress: Callable[[int, int], None],
        lookup_search_settings: LookupSearchSettings,
        company_switch_settings: CompanySwitchSettings | None,
        template_click_service: TemplateClickService | None,
    ) -> None:
        self.image = image_service
        self.stop_event = stop_event
        self.on_status = on_status
        self.on_progress = on_progress
        self.lookup_search_settings = lookup_search_settings
        self.company_switch_settings = company_switch_settings
        self.template_click = template_click_service

    def search_companies(self, jobs: list[Pp30MatchedJob], form_config: Pp30FormConfig) -> None:
        total = len(jobs)
        for index, job in enumerate(jobs, start=1):
            self._check_stop()
            self.on_progress(index, total)
            self.on_status(
                UI_TEXT["pp30_match_log"].format(pdf_name=job.pdf_name, excel_name=job.excel_name)
            )
            if index > 1:
                self._open_next_company_dialog()
            self._search_company(job.excel_name)
            self._open_general_journal()
            self._fill_jv(form_config, job.form_values)
            self._open_payment_journal()
            self._fill_pv(form_config, job.form_values)
            self._capture_reports(form_config, job)
            if index < total:
                self._return_to_company_dialog()
            self.on_status(f"✓ [{index}/{total}] {job.excel_name}")

    def _open_next_company_dialog(self) -> None:
        if self.company_switch_settings is None:
            raise RuntimeError("ยังไม่ได้ตั้งค่าการเปลี่ยนบริษัท")
        open_change_company_menu(self.image, self.company_switch_settings)

    def _search_company(self, excel_name: str) -> None:
        name = excel_name.strip()
        if not name:
            raise RuntimeError("ไม่พบชื่อ Excel สำหรับค้นหา")
        self.on_status(UI_TEXT["pp30_search_log"].format(name=name))
        search_and_select(
            self.image,
            self.lookup_search_settings,
            name,
            template_click=self.template_click,
            on_status=self.on_status,
            should_stop=self.stop_event.is_set,
        )

    def _open_general_journal(self) -> None:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-1")
        self.on_status(f"เปิดเมนู {MENU_GENERAL_JOURNAL_PATH}")
        self.image.wait(0.8)
        open_general_journal_menu(
            self.image,
            self.template_click,
            on_status=self.on_status,
            template_retries=self.lookup_search_settings.template_retries,
            template_retry_delay=self.lookup_search_settings.template_retry_delay,
        )

    def _open_payment_journal(self) -> None:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนู 5-1-2")
        self.on_status(f"เปิดเมนู {MENU_PAYMENT_JOURNAL_PATH}")
        self.image.wait(0.8)
        open_payment_journal_menu(
            self.image,
            self.template_click,
            on_status=self.on_status,
            template_retries=self.lookup_search_settings.template_retries,
            template_retry_delay=self.lookup_search_settings.template_retry_delay,
        )

    def _fill_jv(self, form_config: Pp30FormConfig, values: Pp30FormValues) -> None:
        jv_date = format_express_pv_date(form_config.jv_date)
        sale = self._format_amount(values.vat_sale)
        purchase = self._format_amount(values.vat_purchase)
        self.on_status(UI_TEXT["pp30_jv_log"].format(date=jv_date, sale=sale, purchase=purchase))
        self._new_voucher(jv_date, form_config.jv_description)
        self._type_account(ACCOUNT_PP30_VAT_SALE, enter_count=2, amount=sale)
        self._type_account(ACCOUNT_PP30_VAT_PURCHASE, enter_count=3, amount=purchase)
        self.image.type_text(ACCOUNT_PP30_VAT_PAYABLE, clear_first=False)
        self.image.press("enter", presses=3)
        self.image.press("f2")
        self.image.press("f9")
        self.image.wait(0.3)
        self.image.press("esc", presses=2)
        self.image.wait(0.5)

    def _fill_pv(self, form_config: Pp30FormConfig, values: Pp30FormValues) -> None:
        pv_date = format_express_pv_date(values.pv_date)
        due = self._format_amount(values.amount_due)
        decimal_amount = self._format_amount(values.amount_due_decimal)
        self.on_status(UI_TEXT["pp30_pv_log"].format(date=pv_date, due=due, decimal=decimal_amount))
        self._new_voucher(pv_date, form_config.pv_description)
        self._type_account(ACCOUNT_PP30_VAT_PAYABLE, enter_count=2, amount=due)
        self._type_account(ACCOUNT_PP30_DECIMAL, enter_count=3, amount=decimal_amount)
        self.image.type_text(ACCOUNT_CASH, clear_first=False)
        self.image.press("enter", presses=3)
        self.image.press("f2")
        self.image.press("f9")
        self.image.wait(0.3)

    def _capture_reports(self, form_config: Pp30FormConfig, job: Pp30MatchedJob) -> None:
        if self.template_click is None:
            raise RuntimeError("ต้องเปิด template_click และจับภาพเมนูรายงานบัญชี")
        codes = " ".join(PP30_ACCOUNT_REPORT_CODES)
        self.on_status(UI_TEXT["pp30_report_log"].format(codes=codes))
        jobs = build_ledger_report_jobs(
            report_output_dir=form_config.report_output_dir,
            legal_name=job.excel_name,
            month_date=form_config.jv_date,
            account_codes=PP30_ACCOUNT_REPORT_CODES,
        )
        capture_account_reports(
            self.image,
            self.template_click,
            jobs,
            expand_tree_first=True,
            on_status=self.on_status,
            should_stop=self.stop_event.is_set,
            template_retries=self.lookup_search_settings.template_retries,
            template_retry_delay=self.lookup_search_settings.template_retry_delay,
        )

    def _return_to_company_dialog(self) -> None:
        self.image.press("shift", "f11")
        self.image.wait(0.3)
        self.image.press("tab")
        self.image.press("enter")
        self.image.wait(0.4)

    def _new_voucher(self, voucher_date: str, description: str) -> None:
        self.image.press(*PV_NEW_FILE_KEYS)
        self.image.wait(0.3)
        self.image.press("enter")
        self.image.wait(0.4)
        if voucher_date:
            self.image.type_keys(voucher_date, clear_first=True)
            self.image.wait(0.2)
        self.image.press("enter")
        self.image.wait(0.15)
        if description.strip():
            self.image.type_thai(description.strip(), clear_first=True)
        self.image.press("enter")
        self.image.wait(0.15)

    def _type_account(self, account_code: str, *, enter_count: int, amount: str) -> None:
        self.image.type_text(account_code, clear_first=False)
        self.image.press("enter", presses=enter_count)
        self.image.type_text(amount, clear_first=True)
        self.image.press("enter")

    def _check_stop(self) -> None:
        if self.stop_event.is_set():
            raise InterruptedError("หยุดโดยผู้ใช้")

    @staticmethod
    def _format_amount(value: float) -> str:
        return f"{value:,.2f}"
