from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import UI_TEXT


@dataclass
class Pnd2FormConfig:
    pdf_folder: Path
    pv_date: str
    pdf_files: list[Path] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["pnd2_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["pnd2_pdf_none"])
        if not is_complete_express_date(self.pv_date):
            errors.append(UI_TEXT["pnd2_pv_date_invalid"])
        return errors
