from __future__ import annotations

from dataclasses import dataclass

from constants.routes import INCOME_RV_TAX


@dataclass(frozen=True)
class IncomeFormValues:
    company_name: str
    branch_last5: str
    invoice_date: str
    invoice_number: str
    tax_id: str
    total_amount: float
    wht_amount: float
    vat_amount: float
    bill_count: int
    kind: str = INCOME_RV_TAX

    @property
    def has_total(self) -> bool:
        return abs(self.total_amount) >= 0.005
