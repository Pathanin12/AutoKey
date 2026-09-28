from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.income_form_values import IncomeFormValues


@dataclass(frozen=True)
class IncomePdfRecord:
    pdf_path: Path
    invoices: list[IncomeFormValues]
    has_text: bool = True
    locked: bool = False
