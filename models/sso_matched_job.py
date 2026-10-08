from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.express_company import ExpressCompany
from models.sso_form_values import SsoFormValues


@dataclass(frozen=True)
class SsoMatchedJob:
    pdf_path: Path
    pdf_name: str
    company: ExpressCompany
    form_values: SsoFormValues | None = None
