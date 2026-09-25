from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.express_company import ExpressCompany
from models.pnd3_form_values import Pnd3FormValues


@dataclass(frozen=True)
class Pnd3MatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: Pnd3FormValues | None = None
