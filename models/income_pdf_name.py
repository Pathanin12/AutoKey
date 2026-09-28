from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants.routes import INCOME_PDF_PASSWORD_SEPARATOR


@dataclass(frozen=True)
class IncomePdfName:
    password: str

    @staticmethod
    def parse(pdf_path: Path) -> IncomePdfName:
        _, separator, password = pdf_path.stem.rpartition(INCOME_PDF_PASSWORD_SEPARATOR)
        return IncomePdfName(password=password.strip() if separator else "")
