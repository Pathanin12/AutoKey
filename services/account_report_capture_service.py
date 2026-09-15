from __future__ import annotations

from pathlib import Path
from typing import Callable

from constants.date_utils import express_month_date_range
from constants.routes import (
    ACCOUNT_REPORT_AFTER_F6_WAIT,
    ACCOUNT_REPORT_AFTER_JPEG_WAIT,
    ACCOUNT_REPORT_CAPTURE_WAIT,
    ACCOUNT_REPORT_CODES,
    ACCOUNT_REPORT_FIELD_WAIT,
    ACCOUNT_REPORT_FOCUS_CLICK,
    ACCOUNT_REPORT_JPEG_KEY,
    ACCOUNT_REPORT_JPEG_KEY_PRESSES,
    ACCOUNT_REPORT_MENU_WAIT,
    ACCOUNT_REPORT_PREVIEW_POLL_WAIT,
    ACCOUNT_REPORT_PREVIEW_TIMEOUT,
    ACCOUNT_REPORT_USE_LEGACY_CAPTURE,
    AFTER_SAVE_WAIT,
    COMPANY_DIALOG_WAIT,
    MENU_LEDGER_REPORT_PATH,
)
from constants.template_actions import REPORT_PREVIEW_ACTION_IDS
from models.account_report_capture_job import AccountReportCaptureJob
from models.ka_tam_row import KaTamRow
from models.ledger_range_report_form import LedgerRangeReportForm
from models.report_output_layout import ReportOutputLayout
from models.run_config import RunConfig
from models.window_focus_settings import WindowFocusSettings
from services.account_report_capture_legacy_service import open_ledger_normal_report_menu
from services.image_service import ImageService
from services.template_click_service import TemplateClickService
from services.window_focus_service import focus_express_window


def build_account_report_jobs(config: RunConfig, row: KaTamRow) -> tuple[AccountReportCaptureJob, ...]:
    if config.report_output_dir is None:
        raise RuntimeError("ยังไม่ได้เลือกโฟลเดอร์เก็บไฟล์รายงาน")
    return build_ledger_report_jobs(
        report_output_dir=config.report_output_dir,
        legal_name=row.legal_name,
        month_date=config.pv_date,
        account_codes=ACCOUNT_REPORT_CODES,
    )


def build_ledger_report_jobs(
    *,
    report_output_dir: Path,
    legal_name: str,
    month_date: str,
    account_codes: tuple[str, ...],
    end_month_offset: int = 0,
) -> tuple[AccountReportCaptureJob, ...]:
    start_date, end_date = express_month_date_range(month_date, end_month_offset=end_month_offset)
    layout = ReportOutputLayout(
        base_dir=report_output_dir,
        legal_name=legal_name,
    )
    return tuple(
        AccountReportCaptureJob(
            account_code=code,
            start_date=start_date,
            end_date=end_date,
            output_file=layout.screenshot_path(code),
        )
        for code in account_codes
    )


def should_expand_ledger_report_tree(job_index: int, *, tree_already_open: bool) -> bool:
    return not tree_already_open and job_index == 0


def capture_account_reports(
    image: ImageService,
    template_click: TemplateClickService,
    jobs: tuple[AccountReportCaptureJob, ...] | None = None,
    *,
    month_date: str | None = None,
    expand_tree_first: bool = True,
    return_to_company_dialog: bool = True,
    on_status: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    template_retries: int = 4,
    template_retry_delay: float = 0.15,
    capture_wait: float = ACCOUNT_REPORT_CAPTURE_WAIT,
    field_wait: float = ACCOUNT_REPORT_FIELD_WAIT,
) -> None:
    if ACCOUNT_REPORT_USE_LEGACY_CAPTURE:
        from services.account_report_capture_legacy_service import (
            capture_account_reports as capture_legacy,
        )

        if jobs is None:
            raise RuntimeError("ชุดรายงานเก่าต้องมีรายการรหัสบัญชี")
        capture_legacy(
            image,
            template_click,
            jobs,
            expand_tree_first=expand_tree_first,
            on_status=on_status,
            should_stop=should_stop,
            template_retries=template_retries,
            template_retry_delay=template_retry_delay,
            capture_wait=capture_wait,
            field_wait=field_wait,
        )
        return

    if not month_date:
        raise RuntimeError("ต้องมีวันที่จาก UI สำหรับเรียกรายงาน")
    form = LedgerRangeReportForm.from_ui_date(month_date)
    if on_status:
        on_status(f"แคปรายงาน {form.from_code} {form.to_code}")
    if should_stop and should_stop():
        raise InterruptedError("หยุดโดยผู้ใช้")

    if on_status:
        on_status(f"เปิดเมนู {MENU_LEDGER_REPORT_PATH}")
    open_ledger_normal_report_menu(
        image,
        template_click,
        expand_tree=True,
        on_status=on_status,
        template_retries=template_retries,
        template_retry_delay=template_retry_delay,
        menu_wait=ACCOUNT_REPORT_MENU_WAIT,
    )
    image.wait(field_wait)
    _type_report_field(image, form.from_code)
    _type_report_field(image, form.to_code)
    _type_report_field(image, form.start_date)
    _type_report_field(image, form.end_date)
    image.press("f5")
    image.press("enter")
    if on_status:
        on_status("รอพรีวิวรายงาน")
    template_click.wait_until_first(
        REPORT_PREVIEW_ACTION_IDS,
        timeout=ACCOUNT_REPORT_PREVIEW_TIMEOUT,
        poll_wait=ACCOUNT_REPORT_PREVIEW_POLL_WAIT,
        should_stop=should_stop,
    )
    image.press("f6")
    image.press("enter")
    image.wait(ACCOUNT_REPORT_AFTER_F6_WAIT)
    if on_status:
        on_status("เลือก JPEG")
    template_click.click("report_export_jpeg")
    image.press(ACCOUNT_REPORT_JPEG_KEY, presses=ACCOUNT_REPORT_JPEG_KEY_PRESSES)
    image.press("enter")
    image.wait(ACCOUNT_REPORT_AFTER_JPEG_WAIT)
    _focus_express(image, on_status)
    if return_to_company_dialog:
        _return_to_company_dialog(image)


def _type_report_field(image: ImageService, text: str) -> None:
    image.type_keys(text, clear_first=False)
    image.press("enter")


def _focus_express(image: ImageService, on_status: Callable[[str], None] | None) -> None:
    focused = focus_express_window(WindowFocusSettings(required=False), on_status=on_status)
    if focused:
        return
    image.click_at(*ACCOUNT_REPORT_FOCUS_CLICK)


def _return_to_company_dialog(image: ImageService) -> None:
    image.press("shift", "f11")
    image.wait(AFTER_SAVE_WAIT)
    image.press("tab")
    image.press("enter", presses=2)
    image.wait(COMPANY_DIALOG_WAIT)
