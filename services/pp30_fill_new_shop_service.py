from __future__ import annotations

from typing import Callable

from constants.date_utils import format_express_pv_date
from constants.routes import (
    ACCOUNT_PP30_NEW_SHOP,
    ACCOUNT_PP30_VAT_PURCHASE,
    AFTER_CLOSE_WAIT,
    AFTER_SAVE_WAIT,
    MENU_GENERAL_JOURNAL_PATH,
    MENU_OPEN_PRE_WAIT,
    PP30_NEW_SHOP_REPORT_CODES,
    PV_NEW_FILE_KEYS,
    UI_TEXT,
    VOUCHER_AFTER_DATE_WAIT,
    VOUCHER_AFTER_NEW_WAIT,
    VOUCHER_FIELD_WAIT,
    VOUCHER_FORM_WAIT,
)
from models.pp30_fill_context import Pp30FillContext
from models.pp30_form_config import Pp30FormConfig
from models.pp30_form_values import Pp30FormValues
from services.account_report_capture_service import build_ledger_report_jobs, capture_account_reports
from services.image_service import ImageService
from services.menu_navigation_service import open_general_journal_menu


class Pp30FillNewShopService:
    @staticmethod
    def run(ctx: Pp30FillContext) -> None:
        _open_general_journal(ctx)
        fill_jv(ctx.image, ctx.form_config, ctx.job.form_values, ctx.on_status)
        _capture_reports(ctx)


def fill_jv(
    image: ImageService,
    form_config: Pp30FormConfig,
    values: Pp30FormValues,
    on_status: Callable[[str], None],
) -> None:
    jv_date = format_express_pv_date(form_config.jv_date)
    purchase = _format_amount(values.vat_purchase)
    on_status(UI_TEXT["pp30_jv_new_shop_log"].format(date=jv_date, purchase=purchase))
    _new_voucher(image, jv_date, form_config.jv_description)
    image.type_text(ACCOUNT_PP30_NEW_SHOP, clear_first=False)
    image.press("enter", presses=2)
    image.type_text(purchase, clear_first=True)
    image.press("enter")
    image.type_text(ACCOUNT_PP30_VAT_PURCHASE, clear_first=False)
    image.press("enter", presses=3)
    image.press("f2")
    image.press("f9")
    image.wait(AFTER_SAVE_WAIT)
    image.press("esc", presses=1)
    image.wait(AFTER_CLOSE_WAIT)


def _open_general_journal(ctx: Pp30FillContext) -> None:
    ctx.on_status(f"เปิดเมนู {MENU_GENERAL_JOURNAL_PATH}")
    ctx.image.wait(MENU_OPEN_PRE_WAIT)
    open_general_journal_menu(
        ctx.image,
        ctx.template_click,
        on_status=ctx.on_status,
        template_retries=ctx.template_retries,
        template_retry_delay=ctx.template_retry_delay,
    )


def _new_voucher(image: ImageService, voucher_date: str, description: str) -> None:
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


def _capture_reports(ctx: Pp30FillContext) -> None:
    codes = " ".join(PP30_NEW_SHOP_REPORT_CODES)
    ctx.on_status(UI_TEXT["pp30_report_log"].format(codes=codes))
    jobs = build_ledger_report_jobs(
        report_output_dir=ctx.form_config.report_output_dir,
        legal_name=ctx.job.excel_name,
        month_date=ctx.form_config.jv_date,
        account_codes=PP30_NEW_SHOP_REPORT_CODES,
        end_month_offset=1,
    )
    capture_account_reports(
        ctx.image,
        ctx.template_click,
        jobs,
        expand_tree_first=True,
        on_status=ctx.on_status,
        should_stop=ctx.should_stop,
        template_retries=ctx.template_retries,
        template_retry_delay=ctx.template_retry_delay,
    )


def _format_amount(value: float) -> str:
    return f"{value:,.2f}"
