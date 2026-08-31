from __future__ import annotations

from typing import Callable

from constants.date_utils import express_month_date_range, express_month_folder_name
from constants.routes import ACCOUNT_REPORT_CAPTURE_WAIT, ACCOUNT_REPORT_CODES
from models.account_report_capture_job import AccountReportCaptureJob
from models.ka_tam_row import KaTamRow
from models.report_output_layout import ReportOutputLayout
from models.run_config import RunConfig
from services.image_service import ImageService


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


def capture_account_reports(
    image: ImageService,
    jobs: tuple[AccountReportCaptureJob, ...],
    *,
    on_status: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
    capture_wait: float = ACCOUNT_REPORT_CAPTURE_WAIT,
) -> None:
    for job in jobs:
        if should_stop and should_stop():
            raise InterruptedError("หยุดโดยผู้ใช้")
        if on_status:
            on_status(f"แคปรายงาน {job.account_code}")
        image.press("f12")
        image.wait(0.45)
        image.type_text(job.account_code, clear_first=True)
        image.press("enter")
        image.type_text(job.account_code, clear_first=True)
        image.press("enter")
        image.type_keys(job.start_date, clear_first=True)
        image.press("enter")
        image.type_keys(job.end_date, clear_first=True)
        image.press("enter")
        image.press("f5")
        image.press("enter")
        image.wait(capture_wait)
        saved = image.save_screenshot(job.output_file)
        if on_status:
            on_status(f"บันทึกแคป {job.account_code}: {saved}")
