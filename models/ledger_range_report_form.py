from __future__ import annotations

from dataclasses import dataclass

from constants.date_utils import default_work_date, express_year_start_date
from constants.routes import ACCOUNT_PP30_PENALTY, ACCOUNT_PP30_VAT_PURCHASE


@dataclass(frozen=True)
class LedgerRangeReportForm:
    from_code: str
    to_code: str
    start_date: str
    end_date: str

    @staticmethod
    def from_ui_date(month_date: str) -> LedgerRangeReportForm:
        return LedgerRangeReportForm(
            from_code=ACCOUNT_PP30_VAT_PURCHASE,
            to_code=ACCOUNT_PP30_PENALTY,
            start_date=express_year_start_date(month_date),
            end_date=default_work_date(),
        )
