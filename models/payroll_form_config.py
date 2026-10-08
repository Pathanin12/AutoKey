from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import PAYROLL_DESCRIPTION, UI_TEXT
from models.month_year_period import MonthYearPeriod


@dataclass
class PayrollFormConfig:
    excel_path: Path
    pv_date: str
    period: MonthYearPeriod
    row_count: int = 0

    @property
    def description(self) -> str:
        return PAYROLL_DESCRIPTION.format(period=self.period.text)

    def validate(self) -> list[str]:
        errors: list[str] = []
        path = self.excel_path.expanduser()
        if not str(path).strip() or not path.exists() or not path.is_file():
            errors.append(UI_TEXT["payroll_excel_invalid"])
        elif self.row_count <= 0:
            errors.append(UI_TEXT["payroll_excel_none"])
        if not is_complete_express_date(self.pv_date):
            errors.append(UI_TEXT["payroll_pv_date_invalid"])
        if not self.period.is_valid:
            errors.append(UI_TEXT["payroll_period_invalid"])
        return errors
