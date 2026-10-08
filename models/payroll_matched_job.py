from __future__ import annotations

from dataclasses import dataclass

from models.express_company import ExpressCompany
from models.payroll_row import PayrollRow


@dataclass(frozen=True)
class PayrollMatchedJob:
    row: PayrollRow
    company: ExpressCompany
