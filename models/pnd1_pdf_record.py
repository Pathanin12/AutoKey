from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.pnd1_form_values import Pnd1FormValues


@dataclass(frozen=True)
class Pnd1PdfRecord:
    pdf_path: Path
    company_name: str
    form_values: Pnd1FormValues | None
