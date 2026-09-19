from __future__ import annotations

from typing import Callable

from constants.date_utils import format_express_pv_date
from constants.routes import (
    ACCOUNT_CASH,
    ACCOUNT_PP30_PENALTY,
    ACCOUNT_WT,
    AFTER_CLOSE_WAIT,
    AFTER_SAVE_WAIT,
    MENU_OPEN_PRE_WAIT,
    MENU_PAYMENT_JOURNAL_PATH,
    PND30_LEDGER_REPORT_FROM_CODE,
    PND30_LEDGER_REPORT_TO_CODE,
    UI_TEXT,
    VOUCHER_AFTER_DATE_WAIT,
    VOUCHER_FIELD_WAIT,
    VOUCHER_FORM_WAIT,
    PV_NEW_FILE_KEYS,
    VOUCHER_AFTER_NEW_WAIT,
)
from models.pnd30_fill_context import Pnd30FillContext
from models.pnd30_form_config import Pnd30FormConfig
from models.pnd30_form_values import Pnd30FormValues
from services.account_report_capture_service import capture_account_reports
from services.company_dialog_return_service import return_to_company_dialog
from services.image_service import ImageService
from services.menu_navigation_service import open_payment_journal_menu


class Pnd30FillService:
    @staticmethod
    def run(ctx: Pnd30FillContext) -> None:
        _open_payment_journal(ctx)
        fill_pv(ctx.image, ctx.form_config, ctx.job.form_values, ctx.on_status)
        _capture_reports(ctx)


def fill_pv(
    image: ImageService,
    form_config: Pnd30FormConfig,
    values: Pnd30FormValues,
    on_status: Callable[[str], None],
) -> None:
    pv_date = format_express_pv_date(values.pv_date)
    tax = _format_amount(values.tax_withheld)
    if values.has_surcharge:
        surcharge = _format_amount(values.surcharge)
        on_status(UI_TEXT["pnd30_pv_log"].format(date=pv_date, tax=tax, surcharge=surcharge))
    else:
        on_status(UI_TEXT["pnd30_pv_no_surcharge_log"].format(date=pv_date, tax=tax))
    _start_voucher(image, pv_date, form_config.pv_description)
    image.type_text(ACCOUNT_WT, clear_first=False)
    image.press("enter", presses=2)
    image.type_text(tax, clear_first=True)
    image.press("enter")
    if values.has_surcharge:
        image.type_text(ACCOUNT_PP30_PENALTY, clear_first=False)
        image.press("enter", presses=2)
        image.type_text(_format_amount(values.surcharge), clear_first=True)
        image.press("enter")
    image.type_text(ACCOUNT_CASH, clear_first=False)
    image.press("enter", presses=3)
    image.press("f2")
    image.press("f9")
    image.wait(AFTER_SAVE_WAIT)
    image.press("esc")
    image.wait(AFTER_CLOSE_WAIT)


def _open_payment_journal(ctx: Pnd30FillContext) -> None:
    ctx.on_status(f"เปิดเมนู {MENU_PAYMENT_JOURNAL_PATH}")
    ctx.image.wait(MENU_OPEN_PRE_WAIT)
    open_payment_journal_menu(
        ctx.image,
        ctx.template_click,
        on_status=ctx.on_status,
        template_retries=ctx.template_retries,
        template_retry_delay=ctx.template_retry_delay,
    )


def _start_voucher(image: ImageService, voucher_date: str, description: str) -> None:
    image.press(*PV_NEW_FILE_KEYS)
    image.wait(VOUCHER_AFTER_NEW_WAIT)
    image.press("enter")
    image.wait(VOUCHER_FORM_WAIT)
    if voucher_date:
        image.type_keys(voucher_date, clear_first=True)
        image.wait(VOUCHER_AFTER_DATE_WAIT)
    image.press("enter")
    image.wait(VOUCHER_FIELD_WAIT)
    if description.strip():
        image.type_thai(description.strip(), clear_first=True)
    image.press("enter")
    image.wait(VOUCHER_FIELD_WAIT)


def _capture_reports(ctx: Pnd30FillContext) -> None:
    ctx.on_status(
        UI_TEXT["pp30_report_log"].format(
            codes=f"{PND30_LEDGER_REPORT_FROM_CODE} {PND30_LEDGER_REPORT_TO_CODE}"
        )
    )
    capture_account_reports(
        ctx.image,
        ctx.template_click,
        month_date=ctx.job.form_values.pv_date,
        report_output_dir=ctx.form_config.report_output_dir,
        legal_name=ctx.job.excel_name,
        from_code=PND30_LEDGER_REPORT_FROM_CODE,
        to_code=PND30_LEDGER_REPORT_TO_CODE,
        return_to_company_dialog=False,
        on_status=ctx.on_status,
        should_stop=ctx.should_stop,
        template_retries=ctx.template_retries,
        template_retry_delay=ctx.template_retry_delay,
    )
    ctx.on_status(UI_TEXT["pp30_return_company_log"])
    return_to_company_dialog(ctx.image, enter_presses=1)


def _format_amount(value: float) -> str:
    return f"{value:,.2f}"
