from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.express_company import ExpressCompany
from models.pnd1_form_values import Pnd1FormValues


@dataclass(frozen=True)
class Pnd1MatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: Pnd1FormValues | None = None
