from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.pnd2_form_values import Pnd2FormValues


@dataclass(frozen=True)
class Pnd2PdfRecord:
    pdf_path: Path
    company_name: str
    form_values: Pnd2FormValues | None
