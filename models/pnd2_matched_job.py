from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.express_company import ExpressCompany
from models.pnd2_form_values import Pnd2FormValues


@dataclass(frozen=True)
class Pnd2MatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: Pnd2FormValues | None = None
