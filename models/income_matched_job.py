from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.express_company import ExpressCompany
from models.income_form_values import IncomeFormValues


@dataclass(frozen=True)
class IncomeMatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: IncomeFormValues
