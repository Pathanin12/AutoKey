from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import BT40_PV_DESCRIPTION, BT40_RV_DESCRIPTION, UI_TEXT
from models.month_year_period import MonthYearPeriod


@dataclass
class Bt40FormConfig:
    pdf_folder: Path
    rv_date: str
    period: MonthYearPeriod
    pdf_files: list[Path] = field(default_factory=list)

    @property
    def rv_description(self) -> str:
        return BT40_RV_DESCRIPTION

    @property
    def pv_description(self) -> str:
        return BT40_PV_DESCRIPTION.format(period=self.period.text)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["bt40_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["bt40_pdf_none"])
        if not is_complete_express_date(self.rv_date):
            errors.append(UI_TEXT["bt40_rv_date_invalid"])
        if not self.period.is_valid:
            errors.append(UI_TEXT["bt40_period_invalid"])
        return errors
