from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import UI_TEXT


@dataclass
class KaTamFormConfig:
    excel_path: Path
    pv_date: str
    description: str
    tax_payer_id: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        path = self.excel_path.expanduser()
        if not str(path).strip() or not path.exists() or not path.is_file():
            errors.append(UI_TEXT["ka_tam_excel_invalid"])
        if not is_complete_express_date(self.pv_date):
            errors.append(UI_TEXT["ka_tam_pv_date_invalid"])
        return errors
