from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.pp30_form_values import Pp30FormValues


@dataclass(frozen=True)
class Pp30PdfRecord:
    pdf_path: Path
    company_name: str
    form_values: Pp30FormValues | None = None


@dataclass(frozen=True)
class Pp30MatchedJob:
    pdf_path: Path
    pdf_name: str
    excel_name: str
    form_values: Pp30FormValues
