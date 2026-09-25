from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from constants.routes import UI_TEXT


@dataclass
class Pnd3FormConfig:
    pdf_folder: Path
    description: str
    pdf_files: list[Path] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors: list[str] = []
        folder = self.pdf_folder.expanduser()
        if not str(folder).strip() or not folder.exists() or not folder.is_dir():
            errors.append(UI_TEXT["pnd3_pdf_invalid"])
        elif not self.pdf_files:
            errors.append(UI_TEXT["pnd3_pdf_none"])
        return errors
