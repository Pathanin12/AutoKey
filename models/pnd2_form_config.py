from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.routes import PND2_TAX_DESCRIPTION, UI_TEXT
from models.month_year_period import MonthYearPeriod
from models.pnd2_form_values import Pnd2FormValues
from services.pnd30_extract_service import with_amendment


@dataclass
class Pnd2FormConfig:
    pdf_folder: Path
    period: MonthYearPeriod
    pdf_files: list[Path] = field(default_factory=list)

    def description(self, values: Pnd2FormValues | None = None) -> str:
        text = PND2_TAX_DESCRIPTION.format(period=self.period.text)
        return with_amendment(text, bool(values is not None and values.is_amendment))

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["pnd2_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["pnd2_pdf_none"])
        if not self.period.is_valid:
            errors.append(UI_TEXT["pnd2_period_invalid"])
        return errors
