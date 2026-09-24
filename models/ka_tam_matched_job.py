from __future__ import annotations

from dataclasses import dataclass

from models.express_company import ExpressCompany
from models.ka_tam_row import KaTamRow


@dataclass(frozen=True)
class KaTamMatchedJob:
    row: KaTamRow
    company: ExpressCompany
