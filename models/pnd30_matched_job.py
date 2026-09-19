from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.pnd30_form_values import Pnd30FormValues


@dataclass(frozen=True)
class Pnd30PdfRecord:
    pdf_path: Path
    company_name: str
    form_values: Pnd30FormValues | None = None


@dataclass(frozen=True)
class Pnd30MatchedJob:
    pdf_path: Path
    pdf_name: str
    excel_name: str
    form_values: Pnd30FormValues
