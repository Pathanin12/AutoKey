from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import express_month_year_label, is_complete_express_date
from constants.routes import UI_TEXT
from models.income_form_values import IncomeFormValues
from models.income_lock_mode import IncomeLockMode


@dataclass
class IncomeFormConfig:
    pdf_folder: Path
    excel_path: Path = Path()
    start_date: str = ""
    end_date: str = ""
    pdf_files: list[Path] = field(default_factory=list)
    lock: IncomeLockMode = field(default_factory=lambda: IncomeLockMode.parse(""))
    report_folder: Path = Path()

    @property
    def has_report(self) -> bool:
        return str(self.report_folder).strip() not in ("", ".")

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["income_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["income_pdf_none"])
        if self.has_report and not self.report_folder.expanduser().is_dir():
            errors.append(UI_TEXT["income_report_invalid"])
        if not is_complete_express_date(self.start_date):
            errors.append(UI_TEXT["income_date_invalid"])
        return errors

    def matches_month(self, values: IncomeFormValues) -> bool:
        if not is_complete_express_date(self.start_date):
            return False
        check = values.month_date
        if not is_complete_express_date(check):
            return True
        return express_month_year_label(check) == express_month_year_label(self.start_date)
