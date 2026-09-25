from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.express_company import ExpressCompany
from models.pnd30_form_values import Pnd30FormValues


@dataclass(frozen=True)
class Pnd30MatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: Pnd30FormValues | None = None
