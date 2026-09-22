from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.date_utils import is_complete_express_date
from constants.routes import PP30_RUN_MODES, UI_TEXT
from models.pp30_run_mode import Pp30RunMode


@dataclass
class Pp30FormConfig:
    pdf_folder: Path
    jv_description: str
    pv_description: str
    jv_date: str = ""
    pdf_files: list[Path] = field(default_factory=list)
    run_mode: Pp30RunMode = field(default_factory=Pp30RunMode.normal)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append("กรุณาเลือกโฟลเดอร์ PDF")
        elif not self.pdf_files:
            errors.append("ไม่พบไฟล์ PDF ในโฟลเดอร์นี้")
        if not is_complete_express_date(self.jv_date):
            errors.append(UI_TEXT["pp30_jv_date_invalid"])
        if self.run_mode.key not in PP30_RUN_MODES:
            errors.append(UI_TEXT["pp30_mode_invalid"])
        return errors
