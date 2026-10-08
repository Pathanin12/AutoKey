from __future__ import annotations

from dataclasses import dataclass

from models.express_company import ExpressCompany
from models.wcf_row import WcfRow


@dataclass(frozen=True)
class WcfMatchedJob:
    row: WcfRow
    company: ExpressCompany
