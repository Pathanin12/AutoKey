from __future__ import annotations

from typing import Callable

from constants.date_utils import express_month_date_range, express_month_folder_name
from constants.routes import (
    ACCOUNT_REPORT_CAPTURE_WAIT,
    ACCOUNT_REPORT_CODES,
    ACCOUNT_REPORT_FIELD_WAIT,
    ACCOUNT_REPORT_MENU_WAIT,
)
from models.account_report_capture_job import AccountReportCaptureJob
from models.ka_tam_row import KaTamRow
from models.report_output_layout import ReportOutputLayout
from models.run_config import RunConfig
from services.image_service import ImageService
from services.menu_navigation_service import open_ledger_normal_report_menu
from services.template_click_service import TemplateClickService


def build_account_report_jobs(config: RunConfig, row: KaTamRow) -> tuple[AccountReportCaptureJob, ...]:
    if config.report_output_dir is None:
        raise RuntimeError("ยังไม่ได้เลือกโฟลเดอร์เก็บไฟล์รายงาน")
    start_date, end_date = express_month_date_range(config.pv_date)
    layout = ReportOutputLayout(
        base_dir=config.report_output_dir,
        legal_name=row.legal_name,
        month_folder=express_month_folder_name(config.pv_date),
    )
    return tuple(
        AccountReportCaptureJob(
            account_code=code,
            start_date=start_date,
            end_date=end_date,
            output_file=layout.screenshot_path(code),
        )
        for code in ACCOUNT_REPORT_CODES
    )


def should_expand_ledger_report_tree(job_index: int, *, tree_already_open: bool) -> bool:
    return not tree_already_open and job_index == 0


def capture_account_reports(
    image: ImageService,
    template_click: TemplateClickService,
    jobs: tuple[AccountReportCaptureJob, ...],
    *,
    expand_tree_first: bool = True,
    on_status: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    template_retries: int = 4,
    template_retry_delay: float = 0.15,
    capture_wait: float = ACCOUNT_REPORT_CAPTURE_WAIT,
    field_wait: float = ACCOUNT_REPORT_FIELD_WAIT,
) -> None:
    for index, job in enumerate(jobs):
        if should_stop and should_stop():
            raise InterruptedError("หยุดโดยผู้ใช้")
        if on_status:
            on_status(f"แคปรายงาน {job.account_code}")
        open_ledger_normal_report_menu(
            image,
            template_click,
            expand_tree=should_expand_ledger_report_tree(
                index,
                tree_already_open=not expand_tree_first,
            ),
            on_status=on_status,
            template_retries=template_retries,
            template_retry_delay=template_retry_delay,
            menu_wait=ACCOUNT_REPORT_MENU_WAIT,
        )
        image.wait(field_wait)
        _type_report_field(image, job.account_code)
        _type_report_field(image, job.account_code)
        _type_report_field(image, job.start_date)
        _type_report_field(image, job.end_date)
        image.press("f5")
        image.press("enter")
        image.wait(capture_wait)
        saved = image.save_screenshot(job.output_file)
        if on_status:
            on_status(f"บันทึกแคป {job.account_code}: {saved}")


def _type_report_field(image: ImageService, text: str) -> None:
    image.type_keys(text, clear_first=False)
    image.press("enter")
