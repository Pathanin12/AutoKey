from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.date_utils import express_month_date_range
from constants.routes import PP30_LEDGER_REPORT_FROM_CODE, PP30_LEDGER_REPORT_TO_CODE
from models.report_output_layout import ReportOutputLayout


@dataclass(frozen=True)
class LedgerRangeReportForm:
    from_code: str
    to_code: str
    start_date: str
    end_date: str

    @staticmethod
    def from_ui_date(month_date: str) -> LedgerRangeReportForm:
        start_date, end_date = express_month_date_range(month_date)
        return LedgerRangeReportForm(
            from_code=PP30_LEDGER_REPORT_FROM_CODE,
            to_code=PP30_LEDGER_REPORT_TO_CODE,
            start_date=start_date,
            end_date=end_date,
        )

    def screenshot_path(self, report_output_dir: Path, legal_name: str) -> Path:
        return ReportOutputLayout(
            base_dir=report_output_dir,
            legal_name=legal_name,
        ).screenshot_path(self.from_code)
