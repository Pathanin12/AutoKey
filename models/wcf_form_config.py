from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.routes import UI_TEXT, WCF_DESCRIPTION


@dataclass
class WcfFormConfig:
    excel_path: Path
    row_count: int = 0

    def description_for(self, period: str, dup_n: int | None = None) -> str:
        text = WCF_DESCRIPTION.format(period=period)
        if dup_n:
            return f"{text} *{dup_n}"
        return text

    def validate(self) -> list[str]:
        errors: list[str] = []
        path = self.excel_path.expanduser()
        if not str(path).strip() or not path.exists() or not path.is_file():
            errors.append(UI_TEXT["wcf_excel_invalid"])
        elif self.row_count <= 0:
            errors.append(UI_TEXT["wcf_excel_none"])
        return errors
