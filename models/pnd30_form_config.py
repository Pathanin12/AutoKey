from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.routes import PND30_DESCRIPTION, UI_TEXT
from models.month_year_period import MonthYearPeriod


@dataclass
class Pnd30FormConfig:
    pdf_folder: Path
    period: MonthYearPeriod
    pdf_files: list[Path] = field(default_factory=list)

    @property
    def description(self) -> str:
        return PND30_DESCRIPTION.format(period=self.period.text)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["pnd30_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["pnd30_pdf_none"])
        if not self.period.is_valid:
            errors.append(UI_TEXT["pnd30_period_invalid"])
        return errors
