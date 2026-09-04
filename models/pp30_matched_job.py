from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pp30PdfRecord:
    pdf_path: Path
    company_name: str


@dataclass(frozen=True)
class Pp30MatchedJob:
    pdf_path: Path
    pdf_name: str
    excel_name: str
