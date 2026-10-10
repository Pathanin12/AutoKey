from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.bt40_form_values import Bt40FormValues


@dataclass(frozen=True)
class Bt40PdfRecord:
    pdf_path: Path
    company_name: str
    form_values: Bt40FormValues | None
