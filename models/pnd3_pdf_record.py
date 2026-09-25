from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.pnd3_form_values import Pnd3FormValues


@dataclass(frozen=True)
class Pnd3PdfRecord:
    pdf_path: Path
    company_name: str
    form_values: Pnd3FormValues | None
