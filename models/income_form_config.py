from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import UI_TEXT


@dataclass
class IncomeFormConfig:
    pdf_folder: Path
    excel_path: Path = Path()
    start_date: str = ""
    end_date: str = ""
    pdf_files: list[Path] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        excel = self.excel_path.expanduser()
        if not str(excel).strip() or not excel.exists() or not excel.is_file():
            errors.append(UI_TEXT["income_excel_invalid"])
        if not is_complete_express_date(self.start_date) or not is_complete_express_date(self.end_date):
            errors.append(UI_TEXT["income_date_invalid"])
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["income_pdf_invalid"])
        return errors
