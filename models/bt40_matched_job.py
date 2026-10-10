from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.bt40_form_values import Bt40FormValues
from models.express_company import ExpressCompany


@dataclass(frozen=True)
class Bt40MatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: Bt40FormValues | None = None
