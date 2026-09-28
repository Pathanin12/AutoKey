from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import express_month_year_label, is_complete_express_date
from constants.routes import UI_TEXT
from models.income_form_values import IncomeFormValues


@dataclass
class IncomeFormConfig:
    pdf_folder: Path
    excel_path: Path = Path()
    start_date: str = ""
    end_date: str = ""
    pdf_files: list[Path] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["income_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["income_pdf_none"])
        if not is_complete_express_date(self.start_date):
            errors.append(UI_TEXT["income_date_invalid"])
        return errors

    def matches_month(self, values: IncomeFormValues) -> bool:
        if not is_complete_express_date(self.start_date):
            return False
        if not values.period_date:
            return True
        return express_month_year_label(values.period_date) == express_month_year_label(self.start_date)
