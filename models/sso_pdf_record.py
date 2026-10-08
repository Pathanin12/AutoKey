from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.sso_form_values import SsoFormValues


@dataclass(frozen=True)
class SsoPdfRecord:
    pdf_path: Path
    company_name: str
    form_values: SsoFormValues | None
